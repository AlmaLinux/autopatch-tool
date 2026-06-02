# Autopatch AI Agent

AI-агент на базе Claude Code для автоматического восстановления конфигураций autopatch при сбоях.

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│  HOST (autopatch service)                                       │
│                                                                 │
│  webserv.py                                                     │
│    └─ except → fire_agent()          # src/agent_handler.py     │
│                  └─ Popen(agent_orchestrator.py)  # фоновый     │
│                                                   # процесс     │
│  agent_orchestrator.py (background)  # src/agent_orchestrator.py│
│    1. git clone (SSH)                                           │
│    2. podman run --rm (blocking)                                │
│    3. читает agent_result.json                                  │
│    4. git commit + push (SSH)                                   │
│    5. JSONL лог                                                 │
│    6. Slack (через tools/slack.py)                              │
│    7. cleanup                                                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  CONTAINER (изолированный, без credentials)                     │
│                                                                 │
│  entrypoint.sh                                                  │
│    └─ claude --agent autopatch-fixer                            │
│         ├─ читает error_context.json                            │
│         ├─ анализирует spec + config.yaml                       │
│         ├─ правит config.yaml                                   │
│         ├─ валидирует (autopatch_validate_config, autopatch)    │
│         └─ пишет result/agent_result.json                       │
│                                                                 │
│  Volumes (mounted from host):                                   │
│    /workspace/autopatch/{pkg}/  ← git repo (config.yaml)       │
│    /workspace/rpms/{pkg}/       ← git repo (spec file)         │
│    /workspace/error_context.json ← read-only                   │
│    /workspace/result/           ← agent writes result here     │
│    /home/agent/.claude          ← OAuth session (named volume) │
└─────────────────────────────────────────────────────────────────┘
```

## Структура директории `agent/`

```
agent/
├── README.md                  # Эта документация
├── Containerfile              # OCI-образ (AlmaLinux 10 + Claude Code CLI)
├── entrypoint.sh              # Точка входа контейнера
├── CLAUDE.md                  # Инструкции для Claude Code внутри контейнера
└── .claude/
    ├── settings.json          # Права Claude Code (deny: git push, curl, sudo)
    ├── agents/
    │   ├── autopatch-fixer.md # Основной агент: диагностика → фикс → валидация
    │   └── spec-analyzer.md   # Подагент: анализ spec-файла (read-only)
    ├── skills/
    │   ├── autopatch-config/  # Формат config.yaml, типы actions, примеры
    │   │   └── SKILL.md
    │   └── fix-patterns/      # Паттерны ошибок и способы их исправления
    │       └── SKILL.md
    └── commands/              # Slash-команды
        └── fix-autopatch.md   # Slash-команда /fix-autopatch для ручного запуска
```

## Безопасность

Контейнер **не имеет никаких credentials**:

| Ресурс | Контейнер | Хост |
|--------|-----------|------|
| SSH-ключ | нет | да (git clone/push) |
| Slack-токен | нет | да (из файла `~/.almalinux-debranding-slack/token`) |
| Claude OAuth | volume mount (сессия) | — |

Никаких API-токенов не используется. Git-операции — только через SSH.

Дополнительные ограничения в `.claude/settings.json`:
- **deny**: `git push`, `git remote`, `curl`, `rm -rf`, `sudo`
- **allow**: только `autopatch*`, `grep`, `diff`, `cat`, `ls`

## Хостовые компоненты (вне `agent/`)

| Файл | Описание |
|------|----------|
| `src/agent_handler.py` | Точка входа из Flask: формирует контекст ошибки, запускает фоновый процесс |
| `src/agent_orchestrator.py` | Полный пайплайн: clone → container → push → log → Slack |
| `src/tools/slack.py` | Slack-клиент с функцией `agent_result_message()` |

## Потоки данных

### Входные данные (от autopatch)

Когда autopatch ловит исключение, `agent_handler.py` формирует `error_context`:

```json
{
  "error_type": "ActionNotAppliedError",
  "message": "Action 'replace' was not applied: string not found",
  "traceback": "...",
  "package": "httpd",
  "branch": "c9",
  "timestamp": "2026-03-25T14:30:00+00:00"
}
```

### Выходные данные (от агента)

Агент пишет `/workspace/result/agent_result.json`:

```json
{
  "success": true,
  "summary": "Updated find string in replace action #3 to match new spec",
  "analysis": "Upstream changed 'Requires: foo' to 'Requires: foo-libs'"
}
```

При `success: false`:

```json
{
  "success": false,
  "summary": "Patch context mismatch — requires manual patch regeneration"
}
```

### Ветка (создаётся хостом)

Если `success: true` и не dry-run, оркестратор:
1. Создаёт ветку `agent-fix/{branch}-{timestamp}`
2. Коммитит и пушит по SSH
3. Шлёт в Slack ссылку для создания PR:
   `https://git.almalinux.org/autopatch/{package}/compare/{branch}...agent-fix/{branch}-{timestamp}`

PR создаёт человек через веб-интерфейс Gitea.

### JSONL-лог

Каждый запуск записывается в `/var/log/autopatch/agent_runs.jsonl`:

```json
{
  "package": "httpd",
  "branch": "c9",
  "success": true,
  "branch_name": "agent-fix/c9-20260325-143000",
  "summary": "Updated find string...",
  "duration_sec": 180,
  "error_type": "ActionNotAppliedError",
  "timestamp": "2026-03-25T14:33:00+00:00",
  "dry_run": false
}
```

## Деплой

### Требования

- Podman (уже есть в AlmaLinux по умолчанию)
- SSH-ключ с доступом на запись к `autopatch/*` и `rpms/*` на git.almalinux.org
- Slack-токен в `~/.almalinux-debranding-slack/token` (уже настроен для основного сервиса)
- Одноразовая авторизация Claude Code (OAuth)

### Ansible

Включение агента в `ansible/roles/deploy/defaults/main.yml`:

```yaml
deploy_agent_enabled: true
deploy_agent_dry_run: false    # true — анализ без создания PR
deploy_agent_image: "localhost/autopatch-agent:latest"
deploy_agent_auth_volume: "claude-auth"
```

Никаких дополнительных токенов не нужно — SSH-ключ и Slack-токен уже настроены.

### Первоначальная настройка Claude Code

После первого деплоя нужно авторизовать Claude Code один раз:

```bash
podman run -it \
  -v claude-auth:/home/agent/.claude \
  --entrypoint claude \
  localhost/autopatch-agent:latest \
  login
```

Сессия сохраняется в named volume `claude-auth` и переживает пересборки образа.

### Ручная сборка образа

```bash
podman build -t autopatch-agent -f agent/Containerfile .
```

### Ручной тестовый запуск

```bash
# Подготовка
mkdir -p /tmp/agent-test/{autopatch/httpd,rpms/httpd,result}
git clone git@git.almalinux.org:autopatch/httpd.git /tmp/agent-test/autopatch/httpd
git clone git@git.almalinux.org:rpms/httpd.git /tmp/agent-test/rpms/httpd

cat > /tmp/agent-test/error_context.json <<'EOF'
{
  "error_type": "ActionNotAppliedError",
  "message": "Action 'replace' was not applied: string not found",
  "package": "httpd",
  "branch": "c9"
}
EOF

# Запуск контейнера
podman run --rm \
  -e PACKAGE=httpd \
  -e BRANCH=c9 \
  -e DRY_RUN=true \
  -v claude-auth:/home/agent/.claude \
  -v /tmp/agent-test/autopatch/httpd:/workspace/autopatch/httpd \
  -v /tmp/agent-test/rpms/httpd:/workspace/rpms/httpd \
  -v /tmp/agent-test/error_context.json:/workspace/error_context.json:ro \
  -v /tmp/agent-test/result:/workspace/result \
  localhost/autopatch-agent:latest

# Проверка результата
cat /tmp/agent-test/result/agent_result.json
```

## Dry-run режим

При `AGENT_DRY_RUN=true` (переменная окружения systemd-сервиса):

1. Агент анализирует ошибку и пишет `agent_result.json` **без правки config.yaml**
2. Оркестратор **не пушит ветку**
3. Результат записывается в JSONL-лог с `"dry_run": true`
4. Slack-сообщение содержит `"dry-run"` в тексте

## Тесты

```bash
python -m pytest tests/test_agent.py tests/test_agent_orchestrator.py tests/test_agent_postprocess.py tests/test_agent_webserv.py -v
```

| Файл | Что тестирует |
|------|---------------|
| `tests/test_agent.py` | `fire_agent()`, error context, структура skills/agents |
| `tests/test_agent_orchestrator.py` | Пайплайн: clone, container, push, log, Slack |
| `tests/test_agent_postprocess.py` | JSONL-логирование, Slack (обратная совместимость) |
| `tests/test_agent_webserv.py` | Интеграция webserv.py → agent_handler |
