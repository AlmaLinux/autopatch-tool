"""Tests for the background debranding job (src/debrand_job.py).

debranding has a deep import chain (debranding -> tools.git ->
immudb_wrapper); the notarization modules are stubbed and
apply_modifications is mocked, so no network, git or rpm tooling is touched.
"""

import fcntl
import json
import os
import sys
import threading
import time
import types

import pytest


_STUB_MODULES = ["immudb_wrapper", "immudb", "immudb.client"]


@pytest.fixture
def job(monkeypatch, tmp_path, mocker):
    monkeypatch.setenv("ALLOW_NOTARIZATION", "false")
    monkeypatch.setenv("AGENT_ENABLED", "true")
    monkeypatch.setenv("AUTOPATCH_LOCK_DIR", str(tmp_path / "locks"))
    monkeypatch.delenv("AUTOPATCH_MAX_PARALLEL", raising=False)
    for name in _STUB_MODULES:
        if name not in sys.modules:
            monkeypatch.setitem(sys.modules, name, types.ModuleType(name))

    try:
        import autopatch.debrand_job as job_mod
        import autopatch.debranding as deb_mod
    except ModuleNotFoundError:
        import debrand_job as job_mod
        import debranding as deb_mod

    # launch_agent imports fire_agent from whichever of the two module names
    # resolves first, which depends on how autopatch is installed: patch both.
    fire = mocker.Mock(return_value="123")
    for name in ("agent_handler", "autopatch.agent_handler"):
        try:
            mocker.patch(f"{name}.fire_agent", fire)
        except (ModuleNotFoundError, AttributeError):
            pass

    return types.SimpleNamespace(
        mod=job_mod,
        apply=mocker.patch.object(
            deb_mod, "apply_modifications", return_value=deb_mod.SUCCESS,
        ),
        SUCCESS=deb_mod.SUCCESS,
        success=mocker.patch.object(job_mod.slack_module(), "success_message"),
        failed=mocker.patch.object(job_mod.slack_module(), "failed_message"),
        fire=fire,
        lock_dir=tmp_path / "locks",
    )


class TestRunJob:

    def test_upstream_push_success(self, job):
        result = job.mod.run_job("httpd", "c9", report_branch="c9")

        assert result == job.SUCCESS
        job.apply.assert_called_once_with("httpd", "c9")
        job.success.assert_called_once_with("httpd", "c9")
        job.failed.assert_not_called()
        job.fire.assert_not_called()

    def test_config_push_passes_target_branch(self, job):
        job.mod.run_job(
            "qemu-kvm", "c9-beta",
            target_branch="a9-beta", report_branch="a9-beta",
        )

        job.apply.assert_called_once_with(
            "qemu-kvm", "c9-beta", target_branch="a9-beta",
        )
        job.success.assert_called_once_with("qemu-kvm", "a9-beta")

    def test_report_branch_defaults_to_target_then_upstream(self, job):
        job.mod.run_job("qemu-kvm", "c9-beta", target_branch="a9-beta")
        job.mod.run_job("httpd", "c9")

        assert [c.args for c in job.success.call_args_list] == [
            ("qemu-kvm", "a9-beta"), ("httpd", "c9"),
        ]

    def test_no_slack_message_when_nothing_changed(self, job):
        job.apply.return_value = "Branch is not modified"

        assert job.mod.run_job("httpd", "c9") == "Branch is not modified"
        job.success.assert_not_called()
        job.failed.assert_not_called()

    def test_failure_reports_and_launches_agent(self, job):
        err = RuntimeError("Action 'ReplaceAction' was not applied")
        job.apply.side_effect = err

        result = job.mod.run_job(
            "kernel", "c10", target_branch="a10", report_branch="a10",
        )

        assert result is None
        job.failed.assert_called_once_with("kernel", "a10", str(err))
        # The agent always gets the upstream branch; it maps it back to the
        # config branch the fix PR targets.
        job.fire.assert_called_once_with("kernel", "c10", err)

    def test_failure_skips_agent_when_disabled(self, job, monkeypatch):
        monkeypatch.setenv("AGENT_ENABLED", "false")
        job.apply.side_effect = RuntimeError("boom")

        job.mod.run_job("httpd", "c9")

        job.failed.assert_called_once()
        job.fire.assert_not_called()

    def test_agent_crash_does_not_escape(self, job):
        job.apply.side_effect = RuntimeError("boom")
        job.fire.side_effect = Exception("agent crashed")

        assert job.mod.run_job("httpd", "c9") is None

    def test_slack_outage_does_not_fail_job(self, job):
        job.success.side_effect = Exception("slack down")

        assert job.mod.run_job("httpd", "c9") == job.SUCCESS

    def test_slack_outage_on_failure_still_launches_agent(self, job):
        job.apply.side_effect = RuntimeError("boom")
        job.failed.side_effect = Exception("slack down")

        job.mod.run_job("httpd", "c9")

        job.fire.assert_called_once()

    def test_locks_released_after_failure(self, job):
        job.apply.side_effect = RuntimeError("boom")
        job.mod.run_job("httpd", "c9")

        # A second run of the same package starts instead of waiting forever.
        job.apply.side_effect = None
        assert job.mod.run_job("httpd", "c9") == job.SUCCESS


def _is_locked(path) -> bool:
    with open(path, "w", encoding="utf-8") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fh, fcntl.LOCK_UN)
        return False


class TestLocks:

    def test_package_lock_is_held_inside_the_block(self, job):
        path = job.lock_dir / "package-kernel.lock"
        with job.mod.package_lock("kernel"):
            assert _is_locked(path)
            # Other packages are not blocked.
            assert not _is_locked(job.lock_dir / "package-httpd.lock")
        assert not _is_locked(path)

    def test_same_package_runs_one_at_a_time(self, job):
        order = []

        def slow_apply(package, branch, **kwargs):
            order.append(("start", branch))
            time.sleep(0.3)
            order.append(("end", branch))
            return job.SUCCESS

        job.apply.side_effect = slow_apply
        threads = [
            threading.Thread(target=job.mod.run_job, args=("kernel", b))
            for b in ("c9", "c10")
        ]
        for t in threads:
            t.start()
            time.sleep(0.05)
        for t in threads:
            t.join(timeout=5)

        assert [kind for kind, _ in order] == ["start", "end", "start", "end"]

    def test_run_slots_limit_parallel_jobs(self, job, monkeypatch):
        monkeypatch.setenv("AUTOPATCH_MAX_PARALLEL", "1")
        monkeypatch.setattr(job.mod, "SLOT_POLL_SEC", 0.05)
        running = []
        peak = []

        def slow_apply(package, branch, **kwargs):
            running.append(package)
            peak.append(len(running))
            time.sleep(0.2)
            running.remove(package)
            return job.SUCCESS

        job.apply.side_effect = slow_apply
        threads = [
            threading.Thread(target=job.mod.run_job, args=(pkg, "c9"))
            for pkg in ("kernel", "httpd", "grub2")
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert job.apply.call_count == 3
        assert max(peak) == 1

    def test_invalid_max_parallel_falls_back_to_default(self, job, monkeypatch):
        monkeypatch.setenv("AUTOPATCH_MAX_PARALLEL", "many")
        assert job.mod._max_parallel() == job.mod.DEFAULT_MAX_PARALLEL
        monkeypatch.setenv("AUTOPATCH_MAX_PARALLEL", "0")
        assert job.mod._max_parallel() == 1


class TestEnqueue:

    def test_starts_detached_job_process(self, job, mocker):
        proc = mocker.Mock(returncode=0)
        popen = mocker.patch.object(
            job.mod.subprocess, "Popen", return_value=proc,
        )

        job.mod.enqueue(
            "kernel", "c9", target_branch="a9", report_branch="a9",
        )

        cmd = popen.call_args.args[0]
        assert cmd[0] == sys.executable
        assert cmd[1] == os.path.abspath(job.mod.__file__)
        assert json.loads(cmd[2]) == {
            "package": "kernel",
            "upstream_branch": "c9",
            "target_branch": "a9",
            "report_branch": "a9",
        }
        assert popen.call_args.kwargs["start_new_session"] is True
        proc.wait.assert_called_once()
        job.apply.assert_not_called()

    def test_raises_when_job_process_fails_to_start(self, job, mocker):
        mocker.patch.object(
            job.mod.subprocess, "Popen",
            return_value=mocker.Mock(returncode=1),
        )

        with pytest.raises(RuntimeError, match="kernel"):
            job.mod.enqueue("kernel", "c9")
