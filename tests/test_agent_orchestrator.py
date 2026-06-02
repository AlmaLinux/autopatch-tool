"""Tests for the host-side agent orchestrator pipeline."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from freezegun import freeze_time

from src.agent_orchestrator import (
    _checkout_branches,
    _checkout_reference_branch,
    _clone_repos,
    _commit_and_push,
    _create_pull_request,
    _ensure_remote_branch,
    _format_pr_body,
    _run_container,
    _write_log,
    _send_slack,
    run_pipeline,
)
from src.tools.branch import (
    resolve_config_branch,
    resolve_upstream_branch,
    strip_beta,
    get_sibling_branches,
)


def _ok(**kwargs):
    return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="", **kwargs)


def _fail(**kwargs):
    return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="error", **kwargs)


class TestCloneRepos:

    def test_clones_both_repos(self, mocker, tmp_path):
        mock_run = mocker.patch("src.agent_orchestrator.run_command", return_value=_ok())

        result = _clone_repos(str(tmp_path), "httpd")

        assert result is True
        assert mock_run.call_count == 2
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert any("autopatch/httpd" in " ".join(c) for c in calls)
        assert any("rpms/httpd" in " ".join(c) for c in calls)

    def test_returns_false_on_failure(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator.run_command", return_value=_fail())

        result = _clone_repos(str(tmp_path), "httpd")
        assert result is False

    def test_uses_ssh_urls(self, mocker, tmp_path):
        mock_run = mocker.patch("src.agent_orchestrator.run_command", return_value=_ok())

        _clone_repos(str(tmp_path), "httpd")

        for c in mock_run.call_args_list:
            cmd = c[0][0]
            url = cmd[2]  # git clone <url> <dest>
            assert url.startswith("git@"), f"Expected SSH URL, got: {url}"


class TestResolveConfigBranch:

    def test_c9_becomes_a9(self):
        assert resolve_config_branch("c9") == "a9"

    def test_c9_beta_becomes_a9_beta(self):
        assert resolve_config_branch("c9-beta") == "a9-beta"

    def test_c10s_becomes_a10s(self):
        assert resolve_config_branch("c10s") == "a10s"

    def test_c8_becomes_a8(self):
        assert resolve_config_branch("c8") == "a8"

    def test_target_branch_override(self):
        assert resolve_config_branch("c9", target_branch="custom") == "custom"

    def test_strip_beta(self):
        assert strip_beta("a9-beta") == "a9"

    def test_strip_beta_noop(self):
        assert strip_beta("a9") == "a9"


class TestResolveUpstreamBranch:

    def test_a9_becomes_c9(self):
        assert resolve_upstream_branch("a9") == "c9"

    def test_a9_beta_becomes_c9_beta(self):
        assert resolve_upstream_branch("a9-beta") == "c9-beta"

    def test_a10s_becomes_c10s(self):
        assert resolve_upstream_branch("a10s") == "c10s"

    def test_a8_becomes_c8(self):
        assert resolve_upstream_branch("a8") == "c8"

    def test_roundtrip_with_resolve_config_branch(self):
        for upstream in ("c8", "c9", "c10s", "c9-beta", "c10-beta"):
            assert resolve_upstream_branch(resolve_config_branch(upstream)) == upstream


class TestGetSiblingBranches:

    def test_a10_returns_stream_and_beta(self):
        assert get_sibling_branches("a10") == ["a10s", "a10-beta"]

    def test_a10_beta_returns_stream_and_stable(self):
        assert get_sibling_branches("a10-beta") == ["a10s", "a10"]

    def test_a10s_returns_stable_and_beta(self):
        assert get_sibling_branches("a10s") == ["a10", "a10-beta"]

    def test_a9_returns_stream_and_beta(self):
        assert get_sibling_branches("a9") == ["a9s", "a9-beta"]

    def test_a9_beta_returns_stream_and_stable(self):
        assert get_sibling_branches("a9-beta") == ["a9s", "a9"]

    def test_a8_returns_stream_and_beta(self):
        assert get_sibling_branches("a8") == ["a8s", "a8-beta"]

    def test_unrecognized_returns_empty(self):
        assert get_sibling_branches("custom-branch") == []

    def test_module_stream_branches_ignored(self):
        assert get_sibling_branches("a9-stream-nodejs-20") == []
        assert get_sibling_branches("a8-stream-ruby-3.1") == []
        assert get_sibling_branches("a9-stream-php-8.2") == []


class TestCheckoutReferenceBranch:

    def test_returns_first_available_sibling(self, mocker, tmp_path):
        branch_list = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="  remotes/origin/a10s\n  remotes/origin/a10-beta\n", stderr="",
        )
        mock_run = mocker.patch(
            "src.agent_orchestrator.run_command",
            side_effect=lambda cmd, **kw: branch_list
            if "branch" in cmd
            else _ok(),
        )

        result = _checkout_reference_branch(str(tmp_path), "httpd", "a10")
        assert result == "a10s"
        worktree_calls = [
            c for c in mock_run.call_args_list
            if "worktree" in c[0][0]
        ]
        assert len(worktree_calls) == 1
        assert "a10s" in worktree_calls[0][0][0]

    def test_falls_back_to_second_sibling(self, mocker, tmp_path):
        """If a10s doesn't exist, fall back to a10-beta."""
        branch_list = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="  remotes/origin/a10-beta\n", stderr="",
        )
        mocker.patch(
            "src.agent_orchestrator.run_command",
            side_effect=lambda cmd, **kw: branch_list
            if "branch" in cmd
            else _ok(),
        )

        result = _checkout_reference_branch(str(tmp_path), "httpd", "a10")
        assert result == "a10-beta"

    def test_a10_beta_can_use_a10_as_reference(self, mocker, tmp_path):
        """When running for a10-beta and a10s is absent, use a10."""
        branch_list = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="  remotes/origin/a10\n", stderr="",
        )
        mocker.patch(
            "src.agent_orchestrator.run_command",
            side_effect=lambda cmd, **kw: branch_list
            if "branch" in cmd
            else _ok(),
        )

        result = _checkout_reference_branch(str(tmp_path), "httpd", "a10-beta")
        assert result == "a10"

    def test_a10s_can_use_a10_as_reference(self, mocker, tmp_path):
        branch_list = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="  remotes/origin/a10\n  remotes/origin/a10-beta\n", stderr="",
        )
        mocker.patch(
            "src.agent_orchestrator.run_command",
            side_effect=lambda cmd, **kw: branch_list
            if "branch" in cmd
            else _ok(),
        )

        result = _checkout_reference_branch(str(tmp_path), "httpd", "a10s")
        assert result == "a10"

    def test_returns_none_when_no_siblings_exist(self, mocker, tmp_path):
        branch_list = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="  remotes/origin/a10\n", stderr="",
        )
        mocker.patch(
            "src.agent_orchestrator.run_command",
            return_value=branch_list,
        )
        result = _checkout_reference_branch(str(tmp_path), "httpd", "a10")
        assert result is None

    def test_returns_none_for_unrecognized_branch(self, mocker, tmp_path):
        result = _checkout_reference_branch(str(tmp_path), "httpd", "custom")
        assert result is None

    def test_returns_none_when_worktree_fails(self, mocker, tmp_path):
        branch_list = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="  remotes/origin/a10s\n", stderr="",
        )

        def side_effect(cmd, **kw):
            if "branch" in cmd:
                return branch_list
            if "worktree" in cmd:
                return _fail()
            return _ok()

        mocker.patch("src.agent_orchestrator.run_command", side_effect=side_effect)
        result = _checkout_reference_branch(str(tmp_path), "httpd", "a10")
        assert result is None


class TestCheckoutBranches:

    def test_checks_out_both_branches(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator.run_command", return_value=_ok())

        result = _checkout_branches(str(tmp_path), "httpd", "c9", "a9")
        assert result == "a9"

    def test_falls_back_without_beta(self, mocker, tmp_path):
        call_count = [0]

        def side_effect(cmd, **kwargs):
            call_count[0] += 1
            if cmd[1] == "checkout" and "a9-beta" in cmd:
                return _fail()
            return _ok()

        mocker.patch("src.agent_orchestrator.run_command", side_effect=side_effect)

        result = _checkout_branches(str(tmp_path), "httpd", "c9-beta", "a9-beta")
        assert result == "a9"

    def test_returns_none_when_no_branch_exists(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator.run_command", return_value=_fail())

        result = _checkout_branches(str(tmp_path), "httpd", "c9", "a9")
        assert result is None

    def test_returns_none_when_rpms_branch_missing(self, mocker, tmp_path):
        call_count = [0]

        def side_effect(cmd, **kwargs):
            if "rpms" in kwargs.get("cwd", ""):
                return _fail()
            return _ok()

        mocker.patch("src.agent_orchestrator.run_command", side_effect=side_effect)

        result = _checkout_branches(str(tmp_path), "httpd", "c9", "a9")
        assert result is None


class TestRunContainer:

    def _mock_popen(self, mocker, returncode=0, stdout_data=""):
        """Create a mock Popen that simulates streaming stdout/stderr."""
        import io
        mock_proc = mocker.MagicMock()
        mock_proc.stdout = io.StringIO(stdout_data)
        mock_proc.stderr = io.StringIO("")
        mock_proc.returncode = returncode
        mock_proc.wait = mocker.MagicMock()
        mock_popen = mocker.patch("src.agent_orchestrator.subprocess.Popen",
                                  return_value=mock_proc)
        return mock_popen

    def test_passes_only_safe_env_vars(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator.AGENT_LOG_DIR", str(tmp_path))
        mock_popen = self._mock_popen(mocker)

        _run_container("/tmp/work", "httpd", "c9", "a9", "false",
                       "my-image:v1", "test-auth", 600)

        cmd = mock_popen.call_args[1].get("args") or mock_popen.call_args[0][0]
        cmd_str = " ".join(cmd)
        assert "PACKAGE=httpd" in cmd_str
        assert "BRANCH=c9" in cmd_str
        assert "CONFIG_BRANCH=a9" in cmd_str
        assert "DRY_RUN=false" in cmd_str
        assert "GITEA_TOKEN" not in cmd_str
        assert "SLACK_TOKEN" not in cmd_str

    def test_mounts_volumes(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator.AGENT_LOG_DIR", str(tmp_path))
        mock_popen = self._mock_popen(mocker)

        _run_container("/work", "httpd", "c9", "a9", "false",
                       "img:v1", "auth-vol", 600)

        cmd = mock_popen.call_args[1].get("args") or mock_popen.call_args[0][0]
        cmd_str = " ".join(cmd)
        assert "auth-vol:/home/agent/.claude" in cmd_str
        assert "/work/autopatch/httpd:/workspace/autopatch/httpd" in cmd_str
        assert "/work/rpms/httpd:/workspace/rpms/httpd" in cmd_str
        assert "/work/error_context.json:/workspace/error_context.json:ro" in cmd_str
        assert "/work/result:/workspace/result" in cmd_str

    def test_returns_exit_code_and_stdout(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator.AGENT_LOG_DIR", str(tmp_path))
        self._mock_popen(mocker, returncode=42, stdout_data="some output\n")

        code, stdout = _run_container("/work", "pkg", "c9", "a9", "false", "img", "vol", 60)
        assert code == 42
        assert "some output" in stdout


class TestCommitAndPush:

    def test_creates_branch_commits_pushes(self, mocker, tmp_path):
        autopatch_dir = tmp_path / "autopatch" / "httpd"
        autopatch_dir.mkdir(parents=True)

        mock_run = mocker.patch("src.agent_orchestrator.run_command", return_value=_ok())

        branch_name = _commit_and_push(
            str(tmp_path), "httpd", "c9-beta", "a9",
            {"summary": "fixed replace action"},
        )

        assert branch_name is not None
        assert branch_name.startswith("agent-fix/a9-")
        git_calls = [c[0][0] for c in mock_run.call_args_list]
        ops = [c[1] for c in git_calls]
        assert "checkout" in ops
        assert "add" in ops
        assert "commit" in ops
        assert "push" in ops

    def test_pr_target_branch_overrides_name(self, mocker, tmp_path):
        autopatch_dir = tmp_path / "autopatch" / "httpd"
        autopatch_dir.mkdir(parents=True)
        mocker.patch("src.agent_orchestrator.run_command", return_value=_ok())

        branch_name = _commit_and_push(
            str(tmp_path), "httpd", "c9-beta", "a9",
            {"summary": "fix"}, pr_target_branch="a9-beta",
        )

        assert branch_name.startswith("agent-fix/a9-beta-")

    def test_returns_none_on_commit_failure(self, mocker, tmp_path):
        autopatch_dir = tmp_path / "autopatch" / "httpd"
        autopatch_dir.mkdir(parents=True)

        def side_effect(cmd, **kwargs):
            if cmd[1] == "commit":
                return _fail()
            return _ok()

        mocker.patch("src.agent_orchestrator.run_command", side_effect=side_effect)

        result = _commit_and_push(str(tmp_path), "httpd", "c9", "a9", {"summary": "x"})
        assert result is None

    def test_returns_none_on_push_failure(self, mocker, tmp_path):
        autopatch_dir = tmp_path / "autopatch" / "httpd"
        autopatch_dir.mkdir(parents=True)

        def side_effect(cmd, **kwargs):
            if cmd[1] == "push":
                return _fail()
            return _ok()

        mocker.patch("src.agent_orchestrator.run_command", side_effect=side_effect)

        result = _commit_and_push(str(tmp_path), "httpd", "c9", "a9", {"summary": "x"})
        assert result is None


class TestFormatPrBody:

    def test_minimal_body(self):
        body = _format_pr_body("httpd", "c9", {"summary": "fix"}, {})
        assert "**Summary:** fix" in body
        assert "Root cause" not in body
        assert "Original error" not in body

    def test_includes_analysis(self):
        result = {
            "summary": "Updated find string",
            "analysis": "Upstream changed 'Requires: foo' to 'Requires: foo-libs'",
        }
        body = _format_pr_body("httpd", "c9", result, {})
        assert "### Root cause" in body
        assert "Requires: foo-libs" in body

    def test_includes_error_context(self):
        ctx = {
            "error_type": "ReplaceActionError",
            "traceback": "Traceback (most recent call last):\n  File ...\nValueError: x",
        }
        body = _format_pr_body("httpd", "c9", {"summary": "fix"}, ctx)
        assert "### Original error" in body
        assert "`ReplaceActionError`" in body
        assert "ValueError: x" in body

    def test_truncates_long_traceback(self):
        ctx = {"traceback": "x" * 5000}
        body = _format_pr_body("httpd", "c9", {"summary": "fix"}, ctx)
        assert len(ctx["traceback"]) > 2000
        assert "x" * 2000 in body

    def test_footer_has_package_and_branch(self):
        body = _format_pr_body("kernel", "c10s", {"summary": "fix"}, {})
        assert "Package: `kernel`" in body
        assert "Webhook branch: `c10s`" in body


class TestCreatePullRequest:

    def test_creates_pr_on_success(self, mocker, monkeypatch):
        monkeypatch.setenv("GITEA_TOKEN", "test-token-123")
        mock_post = mocker.patch("src.agent_orchestrator.requests.post")
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "html_url": "https://git.almalinux.org/autopatch/httpd/pulls/42",
        }

        result = _create_pull_request(
            "httpd", "agent-fix/a9-123", "a9",
            {"summary": "fixed replace action"},
        )

        assert result == "https://git.almalinux.org/autopatch/httpd/pulls/42"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"]
        assert payload["head"] == "agent-fix/a9-123"
        assert payload["base"] == "a9"
        assert "httpd" in call_kwargs[1]["json"]["title"] or "httpd" in call_kwargs[0][0]

    def test_body_includes_analysis_and_error(self, mocker, monkeypatch):
        monkeypatch.setenv("GITEA_TOKEN", "tok")
        mock_post = mocker.patch("src.agent_orchestrator.requests.post")
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"html_url": "http://x"}

        _create_pull_request(
            "kernel", "agent-fix/a10s-123", "a10s",
            {"summary": "fix nvidia", "analysis": "Source107 conflict"},
            error_context={"error_type": "ReplaceActionError"},
            webhook_branch="c10s",
        )

        body = mock_post.call_args[1]["json"]["body"]
        assert "Source107 conflict" in body
        assert "`ReplaceActionError`" in body
        assert "Webhook branch: `c10s`" in body

    def test_returns_none_without_token(self, monkeypatch):
        monkeypatch.delenv("GITEA_TOKEN", raising=False)
        result = _create_pull_request(
            "httpd", "agent-fix/a9-123", "a9", {"summary": "fix"},
        )
        assert result is None

    def test_returns_none_on_api_error(self, mocker, monkeypatch):
        monkeypatch.setenv("GITEA_TOKEN", "test-token")
        mock_post = mocker.patch("src.agent_orchestrator.requests.post")
        mock_post.return_value.status_code = 422
        mock_post.return_value.text = "branch already exists"

        result = _create_pull_request(
            "httpd", "agent-fix/a9-123", "a9", {"summary": "fix"},
        )
        assert result is None

    def test_returns_none_on_network_error(self, mocker, monkeypatch):
        monkeypatch.setenv("GITEA_TOKEN", "test-token")
        import requests as req
        mocker.patch(
            "src.agent_orchestrator.requests.post",
            side_effect=req.ConnectionError("timeout"),
        )

        result = _create_pull_request(
            "httpd", "agent-fix/a9-123", "a9", {"summary": "fix"},
        )
        assert result is None

    def test_sends_auth_header(self, mocker, monkeypatch):
        monkeypatch.setenv("GITEA_TOKEN", "my-secret-token")
        mock_post = mocker.patch("src.agent_orchestrator.requests.post")
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"html_url": "http://x"}

        _create_pull_request("pkg", "branch", "a9", {"summary": "fix"})

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "token my-secret-token"


class TestEnsureRemoteBranch:

    def test_noop_when_branches_match(self, mocker, tmp_path):
        mock_run = mocker.patch("src.agent_orchestrator.run_command")
        result = _ensure_remote_branch(str(tmp_path), "httpd", "a9", "a9")
        assert result is True
        mock_run.assert_not_called()

    def test_creates_and_pushes_new_branch(self, mocker, tmp_path):
        mock_run = mocker.patch("src.agent_orchestrator.run_command", return_value=_ok())

        result = _ensure_remote_branch(str(tmp_path), "httpd", "a9-beta", "a9")

        assert result is True
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert ["git", "checkout", "a9"] in calls
        assert ["git", "checkout", "-b", "a9-beta"] in calls
        push_calls = [c for c in calls if c[1] == "push"]
        assert any("a9-beta" in c for c in push_calls)

    def test_returns_false_on_checkout_failure(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator.run_command", return_value=_fail())
        result = _ensure_remote_branch(str(tmp_path), "httpd", "a9-beta", "a9")
        assert result is False

    def test_returns_false_on_push_failure(self, mocker, tmp_path):
        call_count = [0]

        def side_effect(cmd, **kwargs):
            call_count[0] += 1
            if cmd[1] == "push":
                return _fail()
            return _ok()

        mocker.patch("src.agent_orchestrator.run_command", side_effect=side_effect)
        result = _ensure_remote_branch(str(tmp_path), "httpd", "a9-beta", "a9")
        assert result is False


class TestWriteLog:

    @freeze_time("2026-03-25T14:05:00+00:00")
    def test_writes_jsonl_entry(self, tmp_path):
        log_path = str(tmp_path / "logs" / "agent_runs.jsonl")

        _write_log(
            log_path, "httpd", "c9",
            {"success": True, "summary": "Fixed"},
            {"error_type": "ActionNotAppliedError"},
            "agent-fix/c9-20260325-140000",
            False,
            "2026-03-25T14:00:00+00:00",
        )

        log_file = Path(log_path)
        assert log_file.exists()
        entry = json.loads(log_file.read_text().strip())
        assert entry["package"] == "httpd"
        assert entry["branch"] == "c9"
        assert entry["success"] is True
        assert entry["branch_name"] == "agent-fix/c9-20260325-140000"
        assert entry["duration_sec"] == 300
        assert entry["dry_run"] is False

    @freeze_time("2026-03-25T14:05:00+00:00")
    def test_handles_missing_start_ts(self, tmp_path):
        log_path = str(tmp_path / "logs" / "agent_runs.jsonl")
        _write_log(log_path, "pkg", "c9", {"success": False}, {}, None, False, "")
        entry = json.loads(Path(log_path).read_text().strip())
        assert entry["duration_sec"] == 0


class TestSendSlack:

    def test_calls_tools_slack(self, mocker):
        mock_slack = mocker.patch("src.agent_orchestrator.tools_slack")

        _send_slack("httpd", "c9-beta", {"success": True, "summary": "ok"},
                    "agent-fix/a9-123", False, "a9",
                    pr_url="https://git.almalinux.org/autopatch/httpd/pulls/42")

        mock_slack.agent_result_message.assert_called_once_with(
            package="httpd",
            branch="c9-beta",
            success=True,
            summary="ok",
            branch_name="agent-fix/a9-123",
            dry_run=False,
            config_branch="a9",
            pr_url="https://git.almalinux.org/autopatch/httpd/pulls/42",
            pr_blocked=None,
        )

    def test_passes_pr_blocked_through(self, mocker):
        mock_slack = mocker.patch("src.agent_orchestrator.tools_slack")

        _send_slack("qemu-kvm", "c9-beta", {"success": True, "summary": "ok"},
                    "agent-fix/a9-beta-123", False, "a9-beta",
                    pr_url=None, pr_blocked="a9-beta")

        kwargs = mock_slack.agent_result_message.call_args[1]
        assert kwargs["pr_blocked"] == "a9-beta"

    def test_no_crash_when_tools_slack_missing(self, mocker):
        mocker.patch("src.agent_orchestrator.tools_slack", None)
        _send_slack("httpd", "c9", {"success": True}, None, False)

    def test_no_crash_on_slack_error(self, mocker):
        mock_slack = mocker.patch("src.agent_orchestrator.tools_slack")
        mock_slack.agent_result_message.side_effect = Exception("network error")
        _send_slack("httpd", "c9", {"success": True}, None, False)


def _fake_container(result_payload=None):
    """Return a fake _run_container side_effect that writes agent_result.json."""
    payload = result_payload or {"success": True, "summary": "fixed"}

    def _side_effect(work_dir, *_args, **_kwargs):
        result_dir = os.path.join(work_dir, "result")
        os.makedirs(result_dir, exist_ok=True)
        with open(os.path.join(result_dir, "agent_result.json"), "w") as f:
            json.dump(payload, f)
        return 0, ""

    return _side_effect


class TestRunPipeline:

    def test_full_pipeline_success(self, mocker, tmp_path):
        mock_clone = mocker.patch("src.agent_orchestrator._clone_repos",
                                  return_value=True)
        mocker.patch("src.agent_orchestrator._checkout_branches",
                     return_value="a9")
        mocker.patch("src.agent_orchestrator._checkout_reference_branch",
                     return_value=None)
        mocker.patch("src.agent_orchestrator._run_container",
                     side_effect=_fake_container(
                         {"success": True, "summary": "fixed", "analysis": "root cause"},
                     ))
        mock_push = mocker.patch("src.agent_orchestrator._commit_and_push",
                                 return_value="agent-fix/a9-123")
        mock_ensure = mocker.patch("src.agent_orchestrator._ensure_remote_branch",
                                   return_value=True)
        mock_pr = mocker.patch(
            "src.agent_orchestrator._create_pull_request",
            return_value="https://git.almalinux.org/autopatch/httpd/pulls/1",
        )
        mock_log = mocker.patch("src.agent_orchestrator._write_log")
        mocker.patch("src.agent_orchestrator._send_slack")

        run_pipeline(
            "httpd", "c9",
            {"error_type": "RuntimeError", "message": "test"},
            log_path=str(tmp_path / "agent_runs.jsonl"),
        )

        mock_clone.assert_called_once()
        mock_push.assert_called_once()
        mock_ensure.assert_not_called()
        mock_pr.assert_called_once_with(
            "httpd", "agent-fix/a9-123", "a9",
            {"success": True, "summary": "fixed", "analysis": "root cause"},
            error_context={"error_type": "RuntimeError", "message": "test"},
            webhook_branch="c9",
        )
        mock_log.assert_called_once()

    def test_beta_branch_created_for_pr(self, mocker, tmp_path):
        """When c9-beta falls back to a9, PR should target a9-beta after creating it."""
        mocker.patch("src.agent_orchestrator._clone_repos", return_value=True)
        mocker.patch("src.agent_orchestrator._checkout_branches",
                     return_value="a9")
        mocker.patch("src.agent_orchestrator._checkout_reference_branch",
                     return_value=None)
        mocker.patch("src.agent_orchestrator._run_container",
                     side_effect=_fake_container())
        mock_push = mocker.patch("src.agent_orchestrator._commit_and_push",
                                 return_value="agent-fix/a9-beta-123")
        mock_ensure = mocker.patch("src.agent_orchestrator._ensure_remote_branch",
                                   return_value=True)
        mock_pr = mocker.patch("src.agent_orchestrator._create_pull_request",
                               return_value="https://git.almalinux.org/autopatch/qemu-kvm/pulls/1")
        mocker.patch("src.agent_orchestrator._write_log")
        mocker.patch("src.agent_orchestrator._send_slack")

        run_pipeline(
            "qemu-kvm", "c9-beta",
            {"error_type": "RuntimeError"},
            log_path=str(tmp_path / "agent_runs.jsonl"),
        )

        mock_push.assert_called_once()
        push_kwargs = mock_push.call_args
        assert push_kwargs[1]["pr_target_branch"] == "a9-beta"

        mock_ensure.assert_called_once_with(
            mocker.ANY, "qemu-kvm", "a9-beta", "a9",
        )
        mock_pr.assert_called_once()
        pr_args = mock_pr.call_args[0]
        assert pr_args[2] == "a9-beta"

    def test_no_pr_when_beta_target_cannot_be_created(self, mocker, tmp_path):
        """If creating a9-beta fails, no PR is opened (never falls back to a9)."""
        mocker.patch("src.agent_orchestrator._clone_repos", return_value=True)
        mocker.patch("src.agent_orchestrator._checkout_branches",
                     return_value="a9")
        mocker.patch("src.agent_orchestrator._checkout_reference_branch",
                     return_value=None)
        mocker.patch("src.agent_orchestrator._run_container",
                     side_effect=_fake_container())
        mocker.patch("src.agent_orchestrator._commit_and_push",
                     return_value="agent-fix/a9-beta-123")
        mocker.patch("src.agent_orchestrator._ensure_remote_branch",
                     return_value=False)
        mock_pr = mocker.patch("src.agent_orchestrator._create_pull_request",
                               return_value=None)
        mock_log = mocker.patch("src.agent_orchestrator._write_log")
        mock_slack = mocker.patch("src.agent_orchestrator._send_slack")

        run_pipeline(
            "qemu-kvm", "c9-beta",
            {"error_type": "RuntimeError"},
            log_path=str(tmp_path / "agent_runs.jsonl"),
        )

        # PR must NOT be opened into the stable a9 config branch.
        mock_pr.assert_not_called()
        # Pipeline still records the run, with no PR URL.
        assert mock_log.call_args[0][8] is None
        # Maintainers are told the PR was blocked on the beta target branch.
        assert mock_slack.call_args[1]["pr_blocked"] == "a9-beta"

    def test_clone_failure_logs_and_returns(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator._clone_repos", return_value=False)
        mock_log = mocker.patch("src.agent_orchestrator._write_log")
        mocker.patch("src.agent_orchestrator._send_slack")

        run_pipeline(
            "httpd", "c9",
            {"error_type": "RuntimeError"},
            log_path=str(tmp_path / "agent_runs.jsonl"),
        )

        mock_log.assert_called_once()
        result_data = mock_log.call_args[0][3]
        assert result_data["success"] is False

    def test_dry_run_skips_push(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator._clone_repos", return_value=True)
        mocker.patch("src.agent_orchestrator._checkout_branches",
                     return_value="a9")
        mocker.patch("src.agent_orchestrator._checkout_reference_branch",
                     return_value=None)
        mocker.patch("src.agent_orchestrator._run_container",
                     side_effect=_fake_container({"success": True, "summary": "analysis"}))
        mock_push = mocker.patch("src.agent_orchestrator._commit_and_push")
        mocker.patch("src.agent_orchestrator._write_log")
        mocker.patch("src.agent_orchestrator._send_slack")

        run_pipeline(
            "httpd", "c9",
            {"error_type": "RuntimeError"},
            dry_run="true",
            log_path=str(tmp_path / "agent_runs.jsonl"),
        )

        mock_push.assert_not_called()

    def test_checkout_failure_logs_and_returns(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator._clone_repos", return_value=True)
        mocker.patch("src.agent_orchestrator._checkout_branches",
                     return_value=None)
        mock_log = mocker.patch("src.agent_orchestrator._write_log")
        mocker.patch("src.agent_orchestrator._send_slack")

        run_pipeline(
            "httpd", "c9-beta",
            {"error_type": "RuntimeError"},
            log_path=str(tmp_path / "agent_runs.jsonl"),
        )

        mock_log.assert_called_once()
        result_data = mock_log.call_args[0][3]
        assert result_data["success"] is False
        assert "checkout failed" in result_data["summary"].lower()

    def test_rate_limit_detected_in_slack(self, mocker, tmp_path):
        mocker.patch("src.agent_orchestrator._clone_repos", return_value=True)
        mocker.patch("src.agent_orchestrator._checkout_branches",
                     return_value="a9")
        mocker.patch("src.agent_orchestrator._checkout_reference_branch",
                     return_value=None)
        mocker.patch("src.agent_orchestrator._run_container",
                     return_value=(0, "You've hit your limit · resets 2pm (UTC)"))
        mock_log = mocker.patch("src.agent_orchestrator._write_log")
        mocker.patch("src.agent_orchestrator._send_slack")

        run_pipeline(
            "httpd", "c9",
            {"error_type": "RuntimeError"},
            log_path=str(tmp_path / "agent_runs.jsonl"),
        )

        result_data = mock_log.call_args[0][3]
        assert result_data["success"] is False
        assert "rate limit" in result_data["summary"].lower()

    def test_work_dir_kept_for_postmortem(self, mocker, tmp_path):
        """Work dir is NOT deleted immediately — kept for post-mortem inspection."""
        mocker.patch("src.agent_orchestrator._clone_repos", return_value=False)
        mocker.patch("src.agent_orchestrator._write_log")
        mocker.patch("src.agent_orchestrator._send_slack")

        run_pipeline(
            "httpd", "c9",
            {"error_type": "RuntimeError"},
            log_path=str(tmp_path / "agent_runs.jsonl"),
        )

        import glob
        work_dirs = glob.glob(os.path.join(tempfile.gettempdir(), "agent-work-*"))
        assert len(work_dirs) >= 1
