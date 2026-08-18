# Autopatch AI Agent

A Claude Code-based AI agent for automatically recovering autopatch
configurations when they fail.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  HOST (autopatch service)                                       │
│                                                                 │
│  webserv.py                                                     │
│    └─ except → fire_agent()          # src/agent_handler.py     │
│                  └─ Popen(agent_orchestrator.py)  # background  │
│                                                   # process     │
│  agent_orchestrator.py (background)  # src/agent_orchestrator.py│
│    1. git clone (SSH)                                           │
│    2. podman run --rm (blocking)                                │
│    3. reads agent_result.json                                   │
│    4. git commit + push (SSH)                                   │
│    5. JSONL log                                                 │
│    6. Slack (via tools/slack.py)                                │
│    7. cleanup                                                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  CONTAINER (isolated, Claude Code credential only)              │
│                                                                 │
│  entrypoint.sh                                                  │
│    └─ claude --agent autopatch-fixer                            │
│         ├─ reads error_context.json                             │
│         ├─ analyzes spec + config.yaml                          │
│         ├─ edits config.yaml                                    │
│         ├─ validates (autopatch_validate_config, autopatch)     │
│         └─ writes result/agent_result.json                      │
│                                                                 │
│  Volumes (mounted from host):                                   │
│    /workspace/autopatch/{pkg}/  ← git repo (config.yaml)       │
│    /workspace/rpms/{pkg}/       ← git repo (spec file)         │
│    /workspace/error_context.json ← read-only                   │
│    /workspace/result/           ← agent writes result here     │
│    /home/agent/.claude          ← Claude Code config (volume)  │
│  Environment:                                                   │
│    CLAUDE_CODE_OAUTH_TOKEN      ← setup-token (from the host)   │
└─────────────────────────────────────────────────────────────────┘
```

## Layout of the `agent/` directory

```
agent/
├── README.md                  # This documentation
├── Containerfile              # OCI image (AlmaLinux 10 + Claude Code CLI)
├── entrypoint.sh              # Container entry point
├── CLAUDE.md                  # Instructions for Claude Code inside the container
└── .claude/
    ├── settings.json          # Claude Code permissions (deny: git push, curl, sudo)
    ├── agents/
    │   ├── autopatch-fixer.md # Main agent: diagnose → fix → validate
    │   └── spec-analyzer.md   # Sub-agent: spec file analysis (read-only)
    ├── skills/
    │   ├── autopatch-config/  # config.yaml format, action types, examples
    │   │   └── SKILL.md
    │   └── fix-patterns/      # Error patterns and how to fix them
    │       └── SKILL.md
    └── commands/              # Slash commands
        └── fix-autopatch.md   # /fix-autopatch slash command for manual runs
```

## Security

The container gets no autopatch credentials — only what Claude Code itself
needs to authenticate:

| Resource | Container | Host |
|----------|-----------|------|
| SSH key | no | yes (git clone/push) |
| Slack token | no | yes (from `~/.almalinux-debranding-slack/token`) |
| Gitea token | no | yes (opens the fix PR) |
| Claude Code auth | `CLAUDE_CODE_OAUTH_TOKEN`, or the auth volume as fallback | token stored at `~/.claude-code/token.env` (0600) |

The token is passed to podman by name (`-e CLAUDE_CODE_OAUTH_TOKEN`), never as
`-e VAR=value`, so it does not appear in `ps` output. Git operations go over SSH
only.

Additional restrictions in `.claude/settings.json`:
- **deny**: `git push`, `git remote`, `curl`, `rm -rf`, `sudo`
- **allow**: only `autopatch*`, `grep`, `diff`, `cat`, `ls`

## Host components (outside `agent/`)

| File | Description |
|------|-------------|
| `src/agent_handler.py` | Flask entry point: builds the error context, launches the background process |
| `src/agent_orchestrator.py` | Full pipeline: clone → container → push → log → Slack |
| `src/tools/slack.py` | Slack client with the `agent_result_message()` helper |

## Data flows

### Input (from autopatch)

When autopatch raises an exception, `agent_handler.py` builds an `error_context`:

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

### Output (from the agent)

The agent writes `/workspace/result/agent_result.json`:

```json
{
  "success": true,
  "summary": "Updated find string in replace action #3 to match new spec",
  "analysis": "Upstream changed the dependency line:\n\n- `Requires: foo` became `Requires: foo-libs`\n- The replace action's `find` no longer matched, so it was skipped\n\nUpdated `find` to the new wording."
}
```

`summary` and `analysis` are rendered as **Markdown** in the PR description, so
when `analysis` has several points it must be a Markdown list (one point per
line) rather than a single run-on string with `(1) … (2) …`.

On `success: false`:

```json
{
  "success": false,
  "summary": "Patch context mismatch — requires manual patch regeneration"
}
```

### Branch (created by the host)

If `success: true` and not a dry-run, the orchestrator:
1. Creates the branch `agent-fix/{branch}-{timestamp}`
2. Commits and pushes over SSH
3. Sends a Slack message with a link to open the PR:
   `https://git.almalinux.org/autopatch/{package}/compare/{branch}...agent-fix/{branch}-{timestamp}`

A human opens the PR through the Gitea web UI.

### JSONL log

Every run is recorded in `/var/log/autopatch/agent_runs.jsonl`:

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

## Deployment

### Requirements

- Podman (already present on AlmaLinux by default)
- An SSH key with write access to `autopatch/*` and `rpms/*` on git.almalinux.org
- A Slack token at `~/.almalinux-debranding-slack/token` (already set up for the main service)
- Claude Code authentication: a long-lived token from `claude setup-token`
  (deployed by Ansible), or a one-time interactive `claude login`

### Ansible

Enable the agent in `ansible/roles/deploy/defaults/main.yml`:

```yaml
deploy_agent_enabled: true
deploy_agent_dry_run: false    # true — analyze without creating a PR
deploy_agent_image: "localhost/autopatch-agent:latest"
deploy_agent_auth_volume: "claude-auth"
```

The SSH key and Slack token are already configured; the only agent-specific
secret is the Claude Code token below.

### Claude Code authentication

Generate a long-lived token once, on any machine with a Claude subscription:

```bash
claude setup-token
```

Encrypt the printed `sk-ant-oat01-…` value and put it into
`ansible/roles/deploy/vars/main.yml`:

```bash
ansible-vault encrypt_string 'sk-ant-oat01-...' --name claude_code_oauth_token
```

The role writes it to `~/.claude-code/token.env` (0600) on the host, both
systemd units load it with `EnvironmentFile=`, and the orchestrator forwards it
into every agent container. Nothing else is needed — no interactive login, no
session in the volume.

Renew it the same way when it expires: replace the vaulted value and re-deploy.

**Fallback.** With `claude_code_oauth_token` empty, the agent still uses a
session stored in the `claude-auth` volume, created by a one-time login that
survives image rebuilds:

```bash
podman run -it \
  -v claude-auth:/home/agent/.claude \
  --entrypoint claude \
  localhost/autopatch-agent:latest \
  login
```

### Manual image build

```bash
podman build -t autopatch-agent -f agent/Containerfile .
```

### Manual test run

```bash
# Setup
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

# Run the container (the token is taken from the shell environment)
set -a; . ~/.claude-code/token.env; set +a
podman run --rm \
  -e PACKAGE=httpd \
  -e BRANCH=c9 \
  -e DRY_RUN=true \
  -e CLAUDE_CODE_OAUTH_TOKEN \
  -v claude-auth:/home/agent/.claude \
  -v /tmp/agent-test/autopatch/httpd:/workspace/autopatch/httpd \
  -v /tmp/agent-test/rpms/httpd:/workspace/rpms/httpd \
  -v /tmp/agent-test/error_context.json:/workspace/error_context.json:ro \
  -v /tmp/agent-test/result:/workspace/result \
  localhost/autopatch-agent:latest

# Check the result
cat /tmp/agent-test/result/agent_result.json
```

## Dry-run mode

With `AGENT_DRY_RUN=true` (an environment variable of the systemd service):

1. The agent analyzes the error and writes `agent_result.json` **without editing config.yaml**
2. The orchestrator **does not push a branch**
3. The run is recorded in the JSONL log with `"dry_run": true`
4. The Slack message includes `"dry-run"` in its text

## Tests

```bash
python -m pytest tests/test_agent.py tests/test_agent_orchestrator.py tests/test_agent_postprocess.py tests/test_agent_webserv.py -v
```

| File | What it tests |
|------|---------------|
| `tests/test_agent.py` | `fire_agent()`, error context, skills/agents structure |
| `tests/test_agent_orchestrator.py` | Pipeline: clone, container, push, log, Slack |
| `tests/test_agent_postprocess.py` | JSONL logging, Slack (backward compatibility) |
| `tests/test_agent_webserv.py` | webserv.py → agent_handler integration |
