import json
import subprocess
from pathlib import Path

import pytest
from freezegun import freeze_time

from src.agent_handler import _build_error_context, fire_agent


class TestBuildErrorContext:

    def test_action_not_applied(self):
        ActionNotAppliedError = type("ActionNotAppliedError", (RuntimeError,), {})
        err = ActionNotAppliedError("Action 'replace' was not applied: string not found")
        ctx = _build_error_context("httpd", "c9", err)
        assert ctx["error_type"] == "ActionNotAppliedError"
        assert ctx["package"] == "httpd"
        assert ctx["branch"] == "c9"
        assert "not applied" in ctx["message"]
        assert "timestamp" in ctx

    def test_spec_parsing_error(self):
        RPMSpecFileParsingError = type("RPMSpecFileParsingError", (ValueError,), {})
        err = RPMSpecFileParsingError("Failed to parse spec file: missing %prep section")
        ctx = _build_error_context("kernel", "c10", err)
        assert ctx["error_type"] == "RPMSpecFileParsingError"
        assert "spec" in ctx["message"].lower()

    def test_file_not_found(self):
        err = FileNotFoundError("files/missing-cert.cer not found")
        ctx = _build_error_context("shim", "c9", err)
        assert ctx["error_type"] == "FileNotFoundError"
        assert "missing-cert.cer" in ctx["message"]

    def test_generic_runtime_error(self):
        err = RuntimeError("Something went wrong")
        ctx = _build_error_context("bash", "c8", err)
        assert ctx["error_type"] == "RuntimeError"
        assert ctx["package"] == "bash"

    @freeze_time("2026-03-25T14:30:00+00:00")
    def test_timestamp_format(self):
        err = RuntimeError("test")
        ctx = _build_error_context("pkg", "c9", err)
        assert ctx["timestamp"] == "2026-03-25T14:30:00+00:00"


class TestFireAgent:

    def test_spawns_orchestrator(self, mocker, monkeypatch):
        monkeypatch.setenv("AGENT_IMAGE", "my-image:v1")
        monkeypatch.setenv("AGENT_LOG_PATH", "/tmp/logs")
        monkeypatch.setenv("AGENT_AUTH_VOLUME", "test-auth")
        monkeypatch.setenv("AGENT_DRY_RUN", "false")
        monkeypatch.setenv("AGENT_TIMEOUT", "300")

        mock_popen = mocker.patch("src.agent_handler.subprocess.Popen")
        mock_popen.return_value.pid = 12345

        result = fire_agent("httpd", "c9", RuntimeError("test error"))

        assert result == "12345"
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert "agent_orchestrator.py" in cmd[1]

        args_json = json.loads(cmd[2])
        assert args_json["package"] == "httpd"
        assert args_json["branch"] == "c9"
        assert args_json["image"] == "my-image:v1"
        assert args_json["auth_volume"] == "test-auth"
        assert args_json["timeout"] == 300
        assert args_json["error_context"]["error_type"] == "RuntimeError"

    def test_no_secrets_in_args(self, mocker, monkeypatch, tmp_path):
        """Orchestrator args must not contain secrets."""
        monkeypatch.setenv("AGENT_LOG_PATH", str(tmp_path))
        mock_popen = mocker.patch("src.agent_handler.subprocess.Popen")
        mock_popen.return_value.pid = 1

        fire_agent("pkg", "c9", RuntimeError("err"))

        args_json = json.loads(mock_popen.call_args[0][0][2])
        assert "GITEA_TOKEN" not in json.dumps(args_json)
        assert "SLACK_TOKEN" not in json.dumps(args_json)

    def test_passes_dry_run(self, mocker, monkeypatch, tmp_path):
        monkeypatch.setenv("AGENT_DRY_RUN", "true")
        monkeypatch.setenv("AGENT_LOG_PATH", str(tmp_path))

        mock_popen = mocker.patch("src.agent_handler.subprocess.Popen")
        mock_popen.return_value.pid = 1

        fire_agent("pkg", "c9", RuntimeError("x"))

        args_json = json.loads(mock_popen.call_args[0][0][2])
        assert args_json["dry_run"] == "true"

    def test_returns_pid(self, mocker, monkeypatch, tmp_path):
        monkeypatch.setenv("AGENT_LOG_PATH", str(tmp_path))
        mock_popen = mocker.patch("src.agent_handler.subprocess.Popen")
        mock_popen.return_value.pid = 99999

        result = fire_agent("pkg", "c9", RuntimeError("err"))
        assert result == "99999"

    def test_popen_failure_returns_none(self, mocker, monkeypatch):
        mock_popen = mocker.patch("src.agent_handler.subprocess.Popen")
        mock_popen.side_effect = OSError("not found")

        result = fire_agent("pkg", "c9", RuntimeError("err"))
        assert result is None

    def test_error_context_passed_to_orchestrator(self, mocker, monkeypatch, tmp_path):
        monkeypatch.setenv("AGENT_LOG_PATH", str(tmp_path))
        mock_popen = mocker.patch("src.agent_handler.subprocess.Popen")
        mock_popen.return_value.pid = 1

        fire_agent("httpd", "c9", RuntimeError("bad"))

        args_json = json.loads(mock_popen.call_args[0][0][2])
        ctx = args_json["error_context"]
        assert ctx["error_type"] == "RuntimeError"
        assert ctx["package"] == "httpd"
        assert ctx["branch"] == "c9"
        assert "timestamp" in ctx


class TestTemplatesAndSkills:

    def test_all_skills_exist(self):
        for skill in ["autopatch-config", "fix-patterns"]:
            path = Path(f"agent/.claude/skills/{skill}/SKILL.md")
            assert path.exists(), f"Skill {skill} not found"

    def test_agents_have_required_frontmatter(self):
        for agent_file in Path("agent/.claude/agents").glob("*.md"):
            content = agent_file.read_text()
            assert content.startswith("---"), f"{agent_file.name} missing frontmatter"
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"{agent_file.name} incomplete frontmatter"
            frontmatter = parts[1]
            for field in ["name:", "description:", "tools:"]:
                assert field in frontmatter, (
                    f"{agent_file.name} missing {field}"
                )

    def test_pr_creation_is_host_side_only(self):
        """PR creation happens in the orchestrator, not inside the container."""
        content = Path("agent/.claude/agents/autopatch-fixer.md").read_text()
        assert "gitea" not in content.lower()
