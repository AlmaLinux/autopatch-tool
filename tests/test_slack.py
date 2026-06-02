"""Tests for Slack message rendering (src/tools/slack.py).

The module-level ``client`` is a WebClient built with no token (the token
file is absent in CI), so we just patch ``chat_postMessage`` and inspect the
rendered ``text`` — no network calls happen.
"""

from src.tools import slack


def _capture(mocker):
    return mocker.patch.object(slack.client, "chat_postMessage")


class TestAgentResultMessage:

    def test_pr_blocked_message(self, mocker):
        mock_post = _capture(mocker)

        slack.agent_result_message(
            "qemu-kvm", "c9-beta", success=True, summary="fixed",
            branch_name="agent-fix/a9-beta-123", config_branch="a9-beta",
            pr_url=None, pr_blocked="a9-beta",
        )

        text = mock_post.call_args[1]["text"]
        assert "could NOT create" in text
        assert "`a9-beta`" in text
        assert "agent-fix/a9-beta-123" in text
        # Must not emit a (broken) compare link to the non-existent branch.
        assert "compare" not in text

    def test_success_with_pr_url(self, mocker):
        mock_post = _capture(mocker)

        slack.agent_result_message(
            "httpd", "c9", success=True, summary="ok",
            branch_name="agent-fix/a9-1", pr_url="http://pr",
        )

        text = mock_post.call_args[1]["text"]
        assert "PR: http://pr" in text

    def test_success_without_pr_falls_back_to_compare(self, mocker):
        mock_post = _capture(mocker)

        slack.agent_result_message(
            "httpd", "c9", success=True, summary="ok",
            branch_name="agent-fix/a9-1", config_branch="a9",
        )

        text = mock_post.call_args[1]["text"]
        assert "Create PR:" in text
        assert "compare/a9...agent-fix/a9-1" in text
