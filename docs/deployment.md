# Deployment & Operations

How to run Autopatch — as CLI tools, as the webhook service, and as a packaged,
Ansible-deployed system. Also covers RPM packaging and the runtime environment.

## CLI tools

Three console scripts are installed (see [`setup.py`](../setup.py)). From a source
checkout you can call the underlying modules directly.

### `autopatch` — full debranding workflow

Runs the complete workflow (clone `autopatch/<pkg>` and `rpms/<pkg>`, merge the
upstream import, apply the config, commit, tag, push, notarize). This is the same
code path the webhook uses.

```bash
autopatch -p <package> -b <upstream-branch> [options]
# from source:
python autopatch_standalone.py -p <package> -b <upstream-branch> [options]
```

| Flag | Description |
|------|-------------|
| `-p`, `--package` | Package name (required). |
| `-b`, `--branch` | Upstream branch to apply changes from, e.g. `c9` (required). |
| `-t`, `--target-branch` | Target/config branch. Default: auto (`c`→`a`). |
| `--set-custom-tag` | Use a fixed tag instead of the auto-generated one. |
| `--no-tag` | Don't create a git tag. |
| `--debug` | Verbose logging. |

> Requires SSH write access to `git.almalinux.org` and (unless disabled) immudb
> notarization credentials. For local experiments, set `ALLOW_NOTARIZATION=false`.

### `autopatch_package_patching` — apply a config locally

Applies a `config.yaml` to a directory **with no git operations** — useful for
testing a config against a checked-out spec.

```bash
autopatch_package_patching --config path/to/config.yaml --targetdir path/to/package
# from source:
python package_patching.py --config path/to/config.yaml --targetdir path/to/package
```

### `autopatch_validate_config` — validate a config

```bash
autopatch_validate_config path/to/config.yaml
# from source:
python validate_config.py path/to/config.yaml
```

Prints `Config is valid` or the first validation error.

## The webhook service

[`src/webserv.py`](../src/webserv.py) is a Flask app served by gunicorn:

```bash
gunicorn -w 2 --timeout 240 -b 0.0.0.0:80 webserv:app   # run from src/
```

Endpoints (both require the `X-Gitea-Signature` HMAC header, verified against
`AUTH_KEY`):

| Endpoint | Trigger | Purpose |
|----------|---------|---------|
| `POST /debrand_packages` | Gitea *push* webhook on the `rpms` namespace | Debrand the package on the pushed upstream branch. |
| `POST /autopatch_pr_merged` | Gitea *pull request* webhook on the `autopatch` namespace | When a merged **agent-fix** PR closes, re-run debranding. |

### Runtime environment variables

| Variable | Used by | Meaning |
|----------|---------|---------|
| `AUTH_KEY` | webserv | Shared secret for Gitea webhook HMAC. **Required.** |
| `ALLOW_NOTARIZATION` | git tools | `false` disables immudb verify/notarize (default `true`). |
| `AGENT_ENABLED` | webserv | `true` enables the AI recovery agent on failure. |
| `AGENT_DRY_RUN` | agent | `true` = analyze only, no branch/PR. |
| `AGENT_IMAGE` | agent | Container image (default `localhost/autopatch-agent:latest`). |
| `AGENT_AUTH_VOLUME` | agent | Named volume with the Claude Code OAuth session. |
| `AGENT_TIMEOUT` | agent | Container timeout in seconds (default 600). |
| `AGENT_LOG_PATH` | agent | Log directory (default `/var/log/autopatch`). |
| `GITEA_TOKEN` | agent | Token used to open the fix PR via the Gitea API. |

Credentials read from files: immudb/CAS at `~/.cas/credentials`; Slack token at
`~/.almalinux-debranding-slack/token`.

## Ansible deployment

The [`ansible/`](../ansible) role installs dependencies, deploys the source,
saves secrets, optionally builds the agent image, and creates the systemd
service.

### 1. Define secrets

Set the following in `ansible/roles/deploy/vars/main.yml`

### 2. Inventory

```ini
[deploy_servers]
your-server-ip ansible_user=your_user ansible_ssh_private_key_file=your_key
```

### 3. Run

```bash
ansible-playbook -i inventory.ini main.yml
```

### 4. Verify

```bash
systemctl status almalinux-autopatch.service
```

The systemd unit
([template](../ansible/roles/deploy/templates/almalinux-autopatch.service.j2))
runs gunicorn from the deployed `src/` and injects the environment variables
above. Agent variables are only set when `deploy_agent_enabled` is true.

## AI agent container

When the agent is enabled, the recovery container must be built and Claude Code
authorized once:

```bash
# build the image
podman build -t autopatch-agent -f agent/Containerfile .

# one-time OAuth login (session persisted in the named volume)
podman run -it \
  -v claude-auth:/home/agent/.claude \
  --entrypoint claude \
  localhost/autopatch-agent:latest \
  login
```

Full agent design, data flow, manual test runs and dry-run behavior are
documented in [`agent/README.md`](../agent/README.md).

## RPM packaging

A [`Makefile`](../Makefile) builds source and binary RPMs from
[`autopatch.spec`](../autopatch.spec):

```bash
make srpm     # source RPM
make rpm      # binary RPM
make clean
```

The spec produces a metapackage plus sub-packages:

- `autopatch-core` — minimum install: the action engine (`actions_handler.py`),
  the core tools (`tools/rpm.py`, `tools/tools.py`, `tools/logger.py`), and the
  `autopatch` and `autopatch_validate_config` CLIs.
- `autopatch` (main) — adds the git/debranding workflow (`debranding.py`,
  `tools/git.py`, `tools/branch.py`), Slack (`tools/slack.py`), the web service
  (`webserv.py`, `tools/webserv_tools.py`), and the `autopatch_package_patching`
  CLI.

The agent host components (`agent_handler.py`, `agent_orchestrator.py`) are
deployed from source via Ansible and are **deliberately excluded** from the RPM
tarball (see the `--exclude` flags in the `Makefile`).

### Packaging notes

- `python3-slackclient` (for Slack) is not currently in EPEL9.
- `python3-immudb-wrapper` (for notarization) is not yet packaged; the Ansible
  role installs it from git.

## Operational notes

- **Logs:** the service logs to stdout/journald; agent runs additionally write
  per-run logs under `/var/log/autopatch/agent/` and an append-only
  `agent_runs.jsonl`.
- **Notifications:** success/failure and agent results are posted to the
  `almalinux-debranding` Slack channel.
- **Idempotency:** each run resets the AlmaLinux branch to the fresh upstream
  import before applying the config, so re-running is safe.
- **Skipping:** pushes to already-AlmaLinux branches (`a*`) are ignored by
  `/debrand_packages`; packages without an `autopatch` config repo or matching
  branch are skipped.
