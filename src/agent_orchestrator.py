"""
Host-side agent orchestrator.

Runs as a background process spawned by fire_agent().  Handles the full
pipeline: clone repos via SSH, run the container (blocking), read the
result, commit and push the fix branch (SSH), write JSONL log, send
Slack notification via the existing tools.slack module.

The container itself has ZERO credentials — only the Claude Code auth
volume and the mounted work directory.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone

import requests

AGENT_LOG_DIR = "/var/log/autopatch/agent"
WORK_DIR_TTL_SEC = 3600

try:
    from autopatch.tools.logger import logger
    from autopatch.tools.tools import run_command
    from autopatch.tools.branch import resolve_config_branch, strip_beta, get_sibling_branches
    import autopatch.tools.slack as tools_slack
except ImportError:
    import logging

    logger = logging.getLogger("agent_orchestrator")
    logging.basicConfig(level=logging.INFO)
    try:
        from tools.tools import run_command
    except ImportError:
        run_command = None
    try:
        from tools.branch import resolve_config_branch, strip_beta, get_sibling_branches
    except ImportError:
        resolve_config_branch = None
        strip_beta = None
        get_sibling_branches = None
    try:
        import tools.slack as tools_slack
    except ImportError:
        tools_slack = None


def _clone_repos(work_dir: str, package: str) -> bool:
    """Clone autopatch and rpms repos via SSH into work_dir."""
    for ns in ("autopatch", "rpms"):
        dest = os.path.join(work_dir, ns, package)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        url = f"git@git.almalinux.org:{ns}/{package}.git"
        result = run_command(
            ["git", "clone", url, dest],
            raise_on_failure=False,
            timeout=120,
        )
        if result is None or result.returncode != 0:
            return False
    return True


def _fix_volume_permissions(work_dir: str, package: str) -> None:
    """Make all mounted dirs writable by the container's agent user (UID 1000)."""
    for path in (
        os.path.join(work_dir, "autopatch", package),
        os.path.join(work_dir, "rpms", package),
        os.path.join(work_dir, "autopatch_ref", package),
        os.path.join(work_dir, "result"),
    ):
        if os.path.exists(path):
            run_command(
                ["chown", "-R", "1000:1000", path],
                raise_on_failure=False,
            )


def _checkout_branches(
    work_dir: str, package: str, branch: str, config_branch: str,
) -> str | None:
    """Checkout the correct branches after cloning.

    Returns the resolved config_branch on success, None on failure.
    For autopatch repo: tries config_branch, falls back to stripping '-beta'.
    For rpms repo: checks out the original webhook branch.
    """
    autopatch_dir = os.path.join(work_dir, "autopatch", package)
    rpms_dir = os.path.join(work_dir, "rpms", package)

    result = run_command(
        ["git", "checkout", config_branch],
        cwd=autopatch_dir, raise_on_failure=False,
    )
    if result is None or result.returncode != 0:
        if "-beta" in config_branch:
            fallback = strip_beta(config_branch)
            logger.info(
                "Branch %s not found in autopatch repo, trying %s",
                config_branch, fallback,
            )
            result = run_command(
                ["git", "checkout", fallback],
                cwd=autopatch_dir, raise_on_failure=False,
            )
            if result is None or result.returncode != 0:
                logger.error("Branch %s also not found", fallback)
                return None
            config_branch = fallback
        else:
            logger.error("Branch %s not found in autopatch repo", config_branch)
            return None

    result = run_command(
        ["git", "checkout", branch],
        cwd=rpms_dir, raise_on_failure=False,
    )
    if result is None or result.returncode != 0:
        logger.error("Branch %s not found in rpms repo", branch)
        return None

    return config_branch


def _checkout_reference_branch(
    work_dir: str, package: str, config_branch: str,
) -> str | None:
    """Prepare a sibling branch as read-only reference for the agent.

    The orchestrator only makes the data available — the actual comparison
    and fix detection happens inside the agent container (Claude Code).
    Tries siblings in priority order (stream first, then stable/beta) and
    returns the first one that exists in the repo.
    """
    siblings = get_sibling_branches(config_branch)
    if not siblings:
        return None

    autopatch_dir = os.path.join(work_dir, "autopatch", package)

    result = run_command(
        ["git", "branch", "-a"],
        cwd=autopatch_dir, raise_on_failure=False,
    )
    if result is None or result.returncode != 0:
        return None
    remote_branches = result.stdout

    for sibling in siblings:
        if sibling not in remote_branches:
            logger.info(
                "Sibling branch %s not found in autopatch repo, trying next",
                sibling,
            )
            continue

        ref_dir = os.path.join(work_dir, "autopatch_ref", package)
        os.makedirs(os.path.dirname(ref_dir), exist_ok=True)
        wt_result = run_command(
            ["git", "worktree", "add", ref_dir, sibling],
            cwd=autopatch_dir, raise_on_failure=False,
        )
        if wt_result is None or wt_result.returncode != 0:
            logger.warning("Failed to create worktree for reference branch %s", sibling)
            continue

        logger.info("Checked out reference branch %s into %s", sibling, ref_dir)
        return sibling

    logger.info("No sibling branches found for %s", config_branch)
    return None


def _stream_to_logger_and_file(stream, log_file, prefix=""):
    """Read a stream line-by-line, writing to both logger and a file."""
    try:
        for line in stream:
            line_stripped = line.rstrip("\n")
            if prefix:
                logger.info("%s %s", prefix, line_stripped)
            else:
                logger.info(line_stripped)
            log_file.write(line)
            log_file.flush()
    except Exception:
        pass


def _run_container(
    work_dir: str,
    package: str,
    branch: str,
    config_branch: str,
    dry_run: str,
    image: str,
    auth_volume: str,
    timeout: int,
    reference_branch: str | None = None,
) -> tuple[int, str]:
    """Run the agent container (blocking), streaming output to logger and file.

    Returns (exit_code, full_stdout).
    """
    cmd = [
        "podman", "run", "--rm",
        "--security-opt", "label=disable",
        "-e", f"PACKAGE={package}",
        "-e", f"BRANCH={branch}",
        "-e", f"CONFIG_BRANCH={config_branch}",
        "-e", f"DRY_RUN={dry_run}",
        "-v", f"{auth_volume}:/home/agent/.claude",
        "-v", f"{work_dir}/autopatch/{package}:/workspace/autopatch/{package}:z",
        "-v", f"{work_dir}/rpms/{package}:/workspace/rpms/{package}:z",
        "-v", f"{work_dir}/error_context.json:/workspace/error_context.json:ro,z",
        "-v", f"{work_dir}/result:/workspace/result:z",
    ]

    if reference_branch:
        ref_dir = os.path.join(work_dir, "autopatch_ref", package)
        if os.path.isdir(ref_dir):
            cmd += [
                "-e", f"REFERENCE_BRANCH={reference_branch}",
                "-v", f"{ref_dir}:/workspace/autopatch_ref/{package}:ro,z",
            ]

    cmd.append(image)

    log_dir = os.path.join(AGENT_LOG_DIR, package)
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_branch = branch.replace("/", "_")
    stdout_path = os.path.join(log_dir, f"{timestamp}_{safe_branch}_stdout.log")
    stderr_path = os.path.join(log_dir, f"{timestamp}_{safe_branch}_stderr.log")

    logger.info("Container stdout log: %s", stdout_path)

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )

    with open(stdout_path, "w", encoding="utf-8") as out_f, \
         open(stderr_path, "w", encoding="utf-8") as err_f:
        out_thread = threading.Thread(
            target=_stream_to_logger_and_file,
            args=(proc.stdout, out_f, f"[{package}]"),
        )
        err_thread = threading.Thread(
            target=_stream_to_logger_and_file,
            args=(proc.stderr, err_f, f"[{package} stderr]"),
        )
        out_thread.start()
        err_thread.start()

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.error("Container timed out after %ds, killing", timeout)
            proc.kill()
            proc.wait()

        out_thread.join(timeout=5)
        err_thread.join(timeout=5)

    with open(stdout_path, encoding="utf-8") as f:
        full_stdout = f.read()

    return proc.returncode, full_stdout


def _commit_and_push(
    work_dir: str,
    package: str,
    branch: str,
    config_branch: str,
    result_data: dict,
    pr_target_branch: str | None = None,
) -> str | None:
    """Commit changes and push a fix branch via SSH. Returns the branch name."""
    autopatch_dir = os.path.join(work_dir, "autopatch", package)

    run_command(
        ["git", "config", "--global", "--add",
         "safe.directory", autopatch_dir],
        raise_on_failure=False,
    )

    target = pr_target_branch or config_branch
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch_name = f"agent-fix/{target}-{timestamp}"

    run_command(["git", "checkout", "-b", branch_name], cwd=autopatch_dir)
    run_command(["git", "add", "-A"], cwd=autopatch_dir)

    summary = result_data.get("summary", "auto-fix")[:200]
    commit_msg = (
        f"fix(autopatch): auto-fix for {package} on {branch}\n\n{summary}"
    )
    commit_result = run_command(
        ["git", "commit", "-m", commit_msg],
        cwd=autopatch_dir, raise_on_failure=False,
    )
    if commit_result is None or commit_result.returncode != 0:
        return None

    push_result = run_command(
        ["git", "push", "origin", branch_name],
        cwd=autopatch_dir, raise_on_failure=False, timeout=60,
    )
    if push_result is None or push_result.returncode != 0:
        return None

    return branch_name


def _ensure_remote_branch(
    work_dir: str, package: str, target_branch: str, source_branch: str,
) -> bool:
    """Create target_branch from source_branch on remote if they differ.

    Used when e.g. a9-beta doesn't exist — creates it from a9 so the PR
    can target a9-beta.
    """
    if target_branch == source_branch:
        return True

    autopatch_dir = os.path.join(work_dir, "autopatch", package)

    result = run_command(
        ["git", "checkout", source_branch],
        cwd=autopatch_dir, raise_on_failure=False,
    )
    if result is None or result.returncode != 0:
        logger.error("Cannot checkout %s to create %s", source_branch, target_branch)
        return False

    result = run_command(
        ["git", "checkout", "-b", target_branch],
        cwd=autopatch_dir, raise_on_failure=False,
    )
    if result is None or result.returncode != 0:
        logger.error("Cannot create branch %s", target_branch)
        return False

    push_result = run_command(
        ["git", "push", "origin", target_branch],
        cwd=autopatch_dir, raise_on_failure=False, timeout=60,
    )
    if push_result is None or push_result.returncode != 0:
        logger.error("Cannot push branch %s", target_branch)
        return False

    logger.info("Created remote branch %s from %s", target_branch, source_branch)
    return True


GITEA_API_BASE = "https://git.almalinux.org/api/v1"


def _format_pr_body(
    package: str,
    branch: str,
    result_data: dict,
    error_context: dict,
) -> str:
    """Build a detailed PR body from agent result and error context."""
    lines = ["Automated fix by autopatch agent.", ""]

    summary = result_data.get("summary", "N/A")
    lines.append(f"**Summary:** {summary}")

    analysis = result_data.get("analysis")
    if analysis:
        lines += ["", "### Root cause", analysis]

    error_type = error_context.get("error_type")
    traceback_str = error_context.get("traceback")
    if error_type or traceback_str:
        lines += ["", "### Original error"]
        if error_type:
            lines.append(f"**Type:** `{error_type}`")
        if traceback_str:
            tb = traceback_str.strip()
            if len(tb) > 2000:
                tb = tb[-2000:]
            lines += ["", "```", tb, "```"]

    lines += [
        "",
        "---",
        f"Package: `{package}` | Webhook branch: `{branch}`",
    ]

    return "\n".join(lines)


def _create_pull_request(
    package: str,
    branch_name: str,
    config_branch: str,
    result_data: dict,
    *,
    error_context: dict | None = None,
    webhook_branch: str | None = None,
) -> str | None:
    """Create a pull request on Gitea via API. Returns the PR URL or None."""
    token = os.environ.get("GITEA_TOKEN")
    if not token:
        logger.warning("GITEA_TOKEN not set, skipping PR creation")
        return None

    title = f"fix(autopatch): {result_data.get('summary', 'auto-fix')[:120]}"
    body = _format_pr_body(
        package,
        webhook_branch or config_branch,
        result_data,
        error_context or {},
    )

    url = f"{GITEA_API_BASE}/repos/autopatch/{package}/pulls"
    payload = {
        "title": title,
        "head": branch_name,
        "base": config_branch,
        "body": body,
    }
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 201:
            pr_url = resp.json().get("html_url", "")
            logger.info("Created PR: %s", pr_url)
            return pr_url
        logger.error(
            "Gitea PR creation failed: %s %s", resp.status_code, resp.text[:500],
        )
    except requests.RequestException as exc:
        logger.error("Gitea PR request failed: %s", exc)

    return None


def _write_log(
    log_path: str,
    package: str,
    branch: str,
    result_data: dict,
    error_context: dict,
    branch_name: str | None,
    dry_run: bool,
    start_ts: str,
    pr_url: str | None = None,
) -> None:
    """Append a JSONL log entry."""
    duration = 0
    if start_ts:
        try:
            start = datetime.fromisoformat(start_ts)
            duration = (datetime.now(timezone.utc) - start).total_seconds()
        except (ValueError, TypeError):
            pass

    entry = {
        "package": package,
        "branch": branch,
        "success": result_data.get("success", False),
        "branch_name": branch_name,
        "pr_url": pr_url,
        "summary": result_data.get("summary", ""),
        "duration_sec": round(duration),
        "error_type": error_context.get("error_type"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
    }
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _send_slack(
    package: str,
    branch: str,
    result_data: dict,
    branch_name: str | None,
    dry_run: bool,
    config_branch: str | None = None,
    pr_url: str | None = None,
) -> None:
    """Send Slack notification via the existing tools.slack module."""
    if tools_slack is None:
        logger.warning("tools.slack not available, skipping notification")
        return

    try:
        tools_slack.agent_result_message(
            package=package,
            branch=branch,
            success=result_data.get("success", False),
            summary=result_data.get("summary", "unknown"),
            branch_name=branch_name,
            dry_run=dry_run,
            config_branch=config_branch,
            pr_url=pr_url,
        )
    except Exception as exc:
        logger.error("Slack notification failed: %s", exc)


def _remove_worktrees(work_dir: str) -> None:
    """Properly remove any git worktrees before deleting the work dir."""
    autopatch_dir_parent = os.path.join(work_dir, "autopatch")
    ref_dir_parent = os.path.join(work_dir, "autopatch_ref")
    if not os.path.isdir(ref_dir_parent):
        return
    for pkg in os.listdir(ref_dir_parent):
        ref_path = os.path.join(ref_dir_parent, pkg)
        main_repo = os.path.join(autopatch_dir_parent, pkg)
        if os.path.isdir(main_repo):
            run_command(
                ["git", "worktree", "remove", "--force", ref_path],
                cwd=main_repo, raise_on_failure=False,
            )


def _cleanup_old_workdirs() -> None:
    """Remove agent work dirs older than WORK_DIR_TTL_SEC from /tmp."""
    now = time.time()
    tmp = tempfile.gettempdir()
    for name in os.listdir(tmp):
        if not name.startswith("agent-work-"):
            continue
        path = os.path.join(tmp, name)
        try:
            age = now - os.path.getmtime(path)
            if age > WORK_DIR_TTL_SEC:
                _remove_worktrees(path)
                shutil.rmtree(path, ignore_errors=True)
                logger.info("Cleaned up old work dir %s (age=%ds)", path, int(age))
        except OSError:
            pass


def run_pipeline(
    package: str,
    branch: str,
    error_context: dict,
    image: str = "localhost/autopatch-agent:latest",
    auth_volume: str = "claude-auth",
    dry_run: str = "false",
    log_path: str = "/var/log/autopatch/agent_runs.jsonl",
    timeout: int = 600,
) -> None:
    """Full agent pipeline — intended to run in a background process."""
    _cleanup_old_workdirs()

    start_ts = datetime.now(timezone.utc).isoformat()
    is_dry_run = dry_run.lower() == "true"

    work_dir = tempfile.mkdtemp(prefix="agent-work-")
    result_dir = os.path.join(work_dir, "result")
    os.makedirs(result_dir, mode=0o777)

    try:
        with open(
            os.path.join(work_dir, "error_context.json"), "w", encoding="utf-8",
        ) as f:
            json.dump(error_context, f)

        logger.info("Cloning repos for %s/%s...", package, branch)
        if not _clone_repos(work_dir, package):
            result_data = {"success": False, "summary": "Failed to clone repos"}
            _write_log(log_path, package, branch, result_data, error_context,
                       None, is_dry_run, start_ts)
            _send_slack(package, branch, result_data, None, is_dry_run)
            return

        pr_target_branch = resolve_config_branch(branch)
        resolved = _checkout_branches(work_dir, package, branch, pr_target_branch)
        if resolved is None:
            result_data = {
                "success": False,
                "summary": f"Branch checkout failed (tried {pr_target_branch})",
            }
            _write_log(log_path, package, branch, result_data, error_context,
                       None, is_dry_run, start_ts)
            _send_slack(package, branch, result_data, None, is_dry_run)
            return
        config_branch = resolved
        logger.info(
            "Config branch: %s, PR target: %s (webhook: %s)",
            config_branch, pr_target_branch, branch,
        )

        reference_branch = _checkout_reference_branch(
            work_dir, package, config_branch,
        )
        if reference_branch:
            logger.info(
                "Reference branch %s available for comparison", reference_branch,
            )

        _fix_volume_permissions(work_dir, package)

        logger.info("Running agent container (work_dir=%s)...", work_dir)
        exit_code, container_stdout = _run_container(
            work_dir, package, branch, config_branch,
            dry_run, image, auth_volume, timeout,
            reference_branch=reference_branch,
        )
        logger.info("Container exited with code %d", exit_code)

        result_file = os.path.join(result_dir, "agent_result.json")
        if os.path.exists(result_file):
            with open(result_file, encoding="utf-8") as f:
                result_data = json.load(f)
        elif "hit your limit" in container_stdout.lower():
            result_data = {
                "success": False,
                "summary": "Claude Code rate limit reached",
            }
        else:
            result_data = {
                "success": False,
                "summary": f"agent_result.json not found (exit code {exit_code})",
            }

        branch_name = None
        pr_url = None
        if result_data.get("success") and not is_dry_run:
            logger.info("Committing and pushing fix for %s/%s...", package, branch)
            branch_name = _commit_and_push(
                work_dir, package, branch, config_branch, result_data,
                pr_target_branch=pr_target_branch,
            )
            if branch_name:
                logger.info("Pushed branch %s", branch_name)
                actual_pr_target = pr_target_branch
                if pr_target_branch != config_branch:
                    if _ensure_remote_branch(
                        work_dir, package, pr_target_branch, config_branch,
                    ):
                        logger.info(
                            "Created branch %s for PR target",
                            pr_target_branch,
                        )
                    else:
                        logger.warning(
                            "Could not create %s, PR will target %s",
                            pr_target_branch, config_branch,
                        )
                        actual_pr_target = config_branch
                pr_url = _create_pull_request(
                    package, branch_name, actual_pr_target, result_data,
                    error_context=error_context,
                    webhook_branch=branch,
                )
                if not pr_url:
                    logger.warning(
                        "PR not created — manual link: "
                        "https://git.almalinux.org/autopatch/%s/compare/%s...%s",
                        package, actual_pr_target, branch_name,
                    )
            else:
                logger.error("Failed to push fix branch")
        elif result_data.get("success") and is_dry_run:
            logger.info("Dry-run succeeded for %s/%s", package, branch)
        else:
            logger.info("Agent did not produce a successful fix for %s/%s",
                        package, branch)

        _write_log(log_path, package, branch, result_data, error_context,
                   branch_name, is_dry_run, start_ts, pr_url)
        _send_slack(package, branch, result_data, branch_name, is_dry_run,
                    pr_target_branch, pr_url)
    except Exception:
        logger.exception("Orchestrator pipeline failed")
    finally:
        logger.info(
            "Work dir kept for post-mortem: %s (package=%s, branch=%s)",
            work_dir, package, branch,
        )


def main() -> None:
    """CLI entry point — called by agent_handler via subprocess."""
    if len(sys.argv) < 2:
        print("Usage: agent_orchestrator.py <json-args>", file=sys.stderr)
        sys.exit(1)

    args = json.loads(sys.argv[1])
    run_pipeline(
        package=args["package"],
        branch=args["branch"],
        error_context=args["error_context"],
        image=args.get("image", "localhost/autopatch-agent:latest"),
        auth_volume=args.get("auth_volume", "claude-auth"),
        dry_run=args.get("dry_run", "false"),
        log_path=args.get("log_path", "/var/log/autopatch/agent_runs.jsonl"),
        timeout=args.get("timeout", 600),
    )


if __name__ == "__main__":
    main()
