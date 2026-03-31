# AlmaLinux Autopatch Agent

This is an isolated container environment for automatic autopatch failure recovery.

## Working Directory

- `/workspace/` -- root of all operations
- `/workspace/error_context.json` -- error details (type, traceback, package, branch)
- `/workspace/autopatch/{package}/` -- cloned autopatch config repo (mounted from host)
- `/workspace/rpms/{package}/` -- cloned RPM dist-git repo (mounted from host)
- `/workspace/result/` -- output directory (mounted from host)

## Invocation

- Automated: `claude --agent autopatch-fixer -p "..."` -- all instructions are in the agent definition
- Manual: use the `/fix-autopatch` command

## Environment Variables

- `PACKAGE` -- package name (e.g. `httpd`)
- `BRANCH` -- rpms branch from webhook (e.g. `c9-beta`) — upstream spec file is here
- `CONFIG_BRANCH` -- resolved autopatch config branch (e.g. `a9`) — config.yaml is here
- `DRY_RUN` -- if `"true"`, analyze only, do not commit changes

## Important: No Git/Network Operations

This container has NO credentials and NO network access to Gitea.
Your job is ONLY to:
1. Analyze the error and fix `config.yaml`
2. Validate the fix
3. Write the result to `/workspace/result/agent_result.json`

The host system handles all git push and PR creation after the container exits.

## Authentication

Claude Code uses OAuth (session persisted via a mounted volume).
No API key is needed.
