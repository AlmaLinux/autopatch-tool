"""
Fire-and-forget agent launcher.

Builds error context from a caught exception and spawns a background
process that runs the full agent pipeline (clone, container, push, log).
Returns immediately so the Flask handler is never blocked.

The agent container has ZERO credentials — all git operations
happen on the host side via the orchestrator process.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone

try:
    from autopatch.tools.logger import logger
except ImportError:
    from tools.logger import logger


def _build_error_context(
    package: str,
    branch: str,
    error: Exception,
) -> dict:
    return {
        "error_type": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exc(),
        "package": package,
        "branch": branch,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def fire_agent(
    package: str,
    branch: str,
    error: Exception,
) -> str | None:
    """Spawn the agent orchestrator as a background process.

    Returns the PID of the background process on success, or None on failure.
    """
    error_context = _build_error_context(package, branch, error)

    image = os.environ.get("AGENT_IMAGE", "localhost/autopatch-agent:latest")
    log_path = os.environ.get("AGENT_LOG_PATH", "/var/log/autopatch")
    auth_volume = os.environ.get("AGENT_AUTH_VOLUME", "claude-auth")
    dry_run = os.environ.get("AGENT_DRY_RUN", "false")
    timeout = int(os.environ.get("AGENT_TIMEOUT", "600"))

    args_json = json.dumps({
        "package": package,
        "branch": branch,
        "error_context": error_context,
        "image": image,
        "auth_volume": auth_volume,
        "dry_run": dry_run,
        "log_path": os.path.join(log_path, "agent_runs.jsonl"),
        "timeout": timeout,
    })

    orchestrator = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "agent_orchestrator.py"
    )

    try:
        orch_log_dir = os.path.join(log_path, "agent")
        os.makedirs(orch_log_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        safe_branch = branch.replace("/", "_")
        orch_log_file = os.path.join(
            orch_log_dir, f"{ts}_{package}_{safe_branch}_orchestrator.log",
        )
        log_fh = open(orch_log_file, "w", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, orchestrator, args_json],
            stdout=log_fh,
            stderr=log_fh,
            start_new_session=True,
        )
        log_fh.close()
        logger.info(
            "Spawned agent orchestrator PID %s, log: %s",
            proc.pid, orch_log_file,
        )
        return str(proc.pid)
    except OSError as exc:
        logger.error("Failed to spawn agent orchestrator: %s", exc)
        return None
