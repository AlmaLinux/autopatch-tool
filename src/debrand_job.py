"""
Background debranding jobs.

A webhook used to run the whole debranding (clone, actions, commit, push)
inside the HTTP request. Gunicorn kills a sync worker whose request outlives
``--timeout``, and for large packages such as the kernel a run takes several
minutes, so overlapping webhooks were killed mid-run with no Slack message and
no agent. Webhooks now only queue a job: :func:`enqueue` starts this module as
a detached process and returns at once.

Each job takes two locks before it starts:

* a per-package lock, so runs of one package never overlap. A config push and
  an upstream import of the same package used to race and fail on
  ``git push`` or ``git tag``; now the second run starts after the first has
  pushed. Waiting jobs are not ordered, which is fine: every run rebuilds from
  the current config and the current upstream state, so the last one to run
  produces the same result whatever the order.
* one of ``AUTOPATCH_MAX_PARALLEL`` run slots (2 by default), so a burst of
  webhooks for different packages does not clone a dozen repositories at once
  on a small server.

The job reports to Slack and launches the recovery agent on failure, the same
as the synchronous handlers did.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import subprocess
import sys
import time

# First try importing via site-packages path, then try directly from "src".
# Only the logger here: a job may wait a long time for its locks during a mass
# import, and every waiting job is a process, so the heavy modules (Slack SDK,
# git and notarization tooling) are imported once the job actually runs.
try:
    from autopatch.tools.logger import logger
except ImportError:
    from tools.logger import logger

DEFAULT_LOCK_DIR = "/tmp/autopatch-locks"
DEFAULT_MAX_PARALLEL = 2
SLOT_POLL_SEC = 10


def _lock_dir() -> str:
    path = os.environ.get("AUTOPATCH_LOCK_DIR") or DEFAULT_LOCK_DIR
    os.makedirs(path, exist_ok=True)
    return path


def _max_parallel() -> int:
    try:
        value = int(os.environ.get("AUTOPATCH_MAX_PARALLEL", DEFAULT_MAX_PARALLEL))
    except ValueError:
        value = DEFAULT_MAX_PARALLEL
    return max(1, value)


@contextlib.contextmanager
def package_lock(package: str):
    """Hold the package's lock for the duration of the block.

    flock is released by the kernel when the process exits, so a job that
    crashes or is killed never leaves the package locked.
    """
    path = os.path.join(_lock_dir(), f"package-{package}.lock")
    with open(path, "w", encoding="utf-8") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            logger.info(
                "Waiting for the running debranding of %s to finish", package,
            )
            fcntl.flock(fh, fcntl.LOCK_EX)
        yield


@contextlib.contextmanager
def run_slot():
    """Hold one of the run slots for the duration of the block."""
    lock_dir = _lock_dir()
    waiting_logged = False
    while True:
        for slot in range(_max_parallel()):
            fh = open(
                os.path.join(lock_dir, f"slot-{slot}.lock"), "w", encoding="utf-8",
            )
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fh.close()
                continue
            try:
                yield
            finally:
                fh.close()
            return
        if not waiting_logged:
            logger.info("All %d run slots are busy, waiting", _max_parallel())
            waiting_logged = True
        time.sleep(SLOT_POLL_SEC)


def launch_agent(package: str, branch: str, err: Exception) -> None:
    """Start the recovery agent for a failed debranding, if it is enabled.

    ``branch`` is the upstream import branch (c9, c10s, ...): the orchestrator
    checks it out in the rpms repo and maps it to the config branch the fix PR
    targets. Must be called from an ``except`` block: the error context takes
    the current traceback. Never raises.
    """
    if os.environ.get("AGENT_ENABLED", "").lower() != "true":
        return
    if not package or not branch:
        logger.error(
            "Agent not launched, package or branch unknown: "
            "repo name - %s, branch - %s", package, branch,
        )
        return
    try:
        from agent_handler import fire_agent
    except ImportError:
        from autopatch.agent_handler import fire_agent
    try:
        agent_pid = fire_agent(package, branch, err)
        if agent_pid:
            logger.info("Agent launched: pid %s", agent_pid)
    except Exception as agent_err:
        logger.error("Agent launch failed: %s", agent_err)


def slack_module():
    try:
        import autopatch.tools.slack as tools_slack
    except ImportError:
        import tools.slack as tools_slack
    return tools_slack


def _notify(message: str, *args) -> None:
    """Send a Slack message without letting a Slack outage fail the job.

    ``message`` names the function in tools.slack (success_message, ...).
    """
    try:
        getattr(slack_module(), message)(*args)
    except Exception as err:
        logger.error("Slack notification failed: %s", err)


def run_job(
    package: str,
    upstream_branch: str,
    target_branch: str = "",
    report_branch: str = "",
) -> str | None:
    """Run one debranding with locking, Slack reporting and agent launch.

    ``upstream_branch`` is the import branch to debrand from (c9, c10s, ...).
    ``target_branch`` is set for a config push and names the config branch
    that was pushed. ``report_branch`` is the branch shown in Slack.

    Returns the debranding result, or None when it failed.
    """
    report_branch = report_branch or target_branch or upstream_branch
    with package_lock(package), run_slot():
        try:
            from autopatch.debranding import apply_modifications, SUCCESS
        except ImportError:
            from debranding import apply_modifications, SUCCESS
        logger.info(
            "Starting debranding of %s from %s%s", package, upstream_branch,
            f" for config branch {target_branch}" if target_branch else "",
        )
        try:
            if target_branch:
                result = apply_modifications(
                    package, upstream_branch, target_branch=target_branch,
                )
            else:
                result = apply_modifications(package, upstream_branch)
        except Exception as err:
            logger.error(err)
            _notify("failed_message", package, report_branch, str(err))
            launch_agent(package, upstream_branch, err)
            return None

    logger.info(
        "Debranding of %s from %s finished: %s", package, upstream_branch, result,
    )
    if result == SUCCESS:
        _notify("success_message", package, report_branch)
    return result


def enqueue(
    package: str,
    upstream_branch: str,
    target_branch: str = "",
    report_branch: str = "",
) -> None:
    """Start a debranding job in the background and return at once.

    The job process inherits stdout/stderr, so its log goes to the service
    journal like the webhook's own. It forks and exits immediately (see
    :func:`main`), so waiting for it here takes a moment and leaves no zombie
    in the gunicorn worker; the job itself is adopted by init.
    """
    args = json.dumps({
        "package": package,
        "upstream_branch": upstream_branch,
        "target_branch": target_branch,
        "report_branch": report_branch,
    })
    proc = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), args],
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to start the debranding job for {package} "
            f"(exit code {proc.returncode})"
        )
    logger.info(
        "Queued debranding of %s from %s%s", package, upstream_branch,
        f" for config branch {target_branch}" if target_branch else "",
    )


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: debrand_job.py <json-args>", file=sys.stderr)
        sys.exit(1)
    args = json.loads(sys.argv[1])
    # Detach: the parent exits at once so enqueue() returns, and the child
    # runs the job with no process waiting on it.
    if os.fork() > 0:
        os._exit(0)
    try:
        run_job(
            package=args["package"],
            upstream_branch=args["upstream_branch"],
            target_branch=args.get("target_branch", ""),
            report_branch=args.get("report_branch", ""),
        )
    except Exception as err:
        # run_job reports debranding failures itself; this catches the rest
        # (lock directory, imports), which would otherwise only reach the
        # journal as a traceback.
        logger.exception("Debranding job for %s crashed", args["package"])
        _notify(
            "failed_message", args["package"],
            args.get("report_branch") or args["upstream_branch"],
            f"Debranding job crashed: {err}",
        )


if __name__ == "__main__":
    main()
