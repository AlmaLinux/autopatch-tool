#!/bin/bash
set -euo pipefail

for var in PACKAGE BRANCH CONFIG_BRANCH; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: Required environment variable $var is not set" >&2
        exit 1
    fi
done

CLAUDE_DIR="$HOME/.claude"
if [ ! -d "$CLAUDE_DIR" ] || [ -z "$(ls -A "$CLAUDE_DIR" 2>/dev/null)" ]; then
    echo "ERROR: Claude Code auth not found. Run the login command first." >&2
    exit 1
fi

CLAUDE_JSON="$HOME/.claude.json"
if [ ! -f "$CLAUDE_JSON" ]; then
    BACKUP=$(find "$CLAUDE_DIR/backups" -name '.claude.json.backup.*' -type f 2>/dev/null | sort | tail -1)
    if [ -n "$BACKUP" ]; then
        cp "$BACKUP" "$CLAUDE_JSON"
    fi
fi

echo "=== Autopatch Agent: $PACKAGE @ $BRANCH (config: $CONFIG_BRANCH) ==="

DRY_RUN="${DRY_RUN:-false}"
REFERENCE_BRANCH="${REFERENCE_BRANCH:-}"

PROMPT="Fix autopatch failure for package \"${PACKAGE}\" on branch \"${BRANCH}\".
The autopatch config branch is \"${CONFIG_BRANCH}\" (config.yaml lives here).
The rpms branch is \"${BRANCH}\" (upstream spec file lives here).
Error context: /workspace/error_context.json
DRY_RUN=${DRY_RUN}"

if [ -n "$REFERENCE_BRANCH" ]; then
    PROMPT="${PROMPT}
REFERENCE_BRANCH=${REFERENCE_BRANCH}
Reference config from the stream branch is available at /workspace/autopatch_ref/${PACKAGE}/ (read-only).
Check it FIRST — the stream branch often already has the fix you need."
fi

RESULT_FILE="/workspace/result/agent_result.json"
STDOUT_LOG="/workspace/result/claude_stdout.log"

if ! touch "$STDOUT_LOG" 2>/dev/null; then
    STDOUT_LOG="/tmp/claude_stdout.log"
    echo "WARNING: /workspace/result/ not writable, using $STDOUT_LOG"
fi

echo "Running Claude Code agent..."
set +e
claude --agent autopatch-fixer \
    -p "$PROMPT" \
    --permission-mode bypassPermissions 2>&1 | tee "$STDOUT_LOG"
AGENT_EXIT=${PIPESTATUS[0]}
set -e

echo "=== Agent finished (exit code: $AGENT_EXIT) ==="

if [ ! -f "$RESULT_FILE" ]; then
    echo "WARNING: agent_result.json not found, generating fallback from stdout"
    LAST_MSG=$(tail -80 "$STDOUT_LOG" | head -c 3000 || true)
    ESCAPED=$(echo "$LAST_MSG" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read())[1:-1])' 2>/dev/null || echo "could not parse stdout")
    cat > "$RESULT_FILE" <<EOFJ
{
  "success": false,
  "summary": "agent_result.json not written by Claude Code (exit code ${AGENT_EXIT})",
  "analysis": "${ESCAPED}",
  "fallback": true
}
EOFJ
    echo "Fallback result written to $RESULT_FILE"
fi

exit $AGENT_EXIT
