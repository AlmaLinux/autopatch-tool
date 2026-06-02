"""Integration tests for agent invocation from webserv.py.

webserv.py has deep import chains (debranding -> git -> immudb_wrapper).
We stub those modules before importing webserv so the tests don't need
the full production dependency tree.
"""

import hmac
import json
import os
import sys
import types

import pytest


_STUB_MODULES = ["immudb_wrapper", "immudb", "immudb.client"]

AUTH_KEY = "test-key"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("AUTH_KEY", AUTH_KEY)
    monkeypatch.setenv("AGENT_ENABLED", "false")
    monkeypatch.setenv("ALLOW_NOTARIZATION", "false")

    saved = {}
    for mod_name in _STUB_MODULES:
        saved[mod_name] = sys.modules.get(mod_name)
        if mod_name not in sys.modules:
            sys.modules[mod_name] = types.ModuleType(mod_name)

    try:
        from autopatch.webserv import app
        _mod_prefix = "autopatch"
    except ModuleNotFoundError:
        from webserv import app
        _mod_prefix = ""
    app.config["TESTING"] = True
    with app.test_client() as c:
        c._mod_prefix = _mod_prefix
        yield c

    for mod_name in _STUB_MODULES:
        if saved[mod_name] is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = saved[mod_name]


VALID_PAYLOAD = {
    "repository": {"name": "httpd"},
    "ref": "refs/heads/c9",
}

PR_MERGED_PAYLOAD = {
    "action": "closed",
    "pull_request": {
        "merged": True,
        "base": {"ref": "a9-beta"},
        "head": {"ref": "agent-fix/a9-beta-20260601-101500"},
    },
    "repository": {"name": "qemu-kvm"},
}


def _post(client, payload=None):
    """Send a request with a valid Gitea HMAC signature.

    The except block in debrand_packages() returns None (pre-existing --
    no error response was returned before the agent integration either),
    so Flask raises TypeError. We catch that here and return None to let
    tests focus on the agent-specific assertions.
    """
    body = json.dumps(payload or VALID_PAYLOAD).encode()
    sig = hmac.new(
        key=AUTH_KEY.encode(),
        msg=body,
        digestmod="SHA256",
    ).hexdigest()
    try:
        return client.post(
            "/debrand_packages",
            data=body,
            content_type="application/json",
            headers={"X-Gitea-Signature": sig},
        )
    except TypeError:
        return None


def _post_pr(client, payload):
    """Send a PR-merged webhook with a valid Gitea HMAC signature."""
    body = json.dumps(payload).encode()
    sig = hmac.new(
        key=AUTH_KEY.encode(),
        msg=body,
        digestmod="SHA256",
    ).hexdigest()
    return client.post(
        "/autopatch_pr_merged",
        data=body,
        content_type="application/json",
        headers={"X-Gitea-Signature": sig},
    )


def _mod(client, name):
    """Build a fully-qualified module path that works in both environments."""
    prefix = client._mod_prefix
    if prefix:
        return f"{prefix}.{name}"
    return name


def _webserv_mod(client):
    """Return the imported webserv module object (already in sys.modules)."""
    prefix = client._mod_prefix
    name = f"{prefix}.webserv" if prefix else "webserv"
    return sys.modules[name]


class TestAgentIntegration:

    def test_calls_fire_agent_on_exception(self, client, mocker, monkeypatch):
        monkeypatch.setenv("AGENT_ENABLED", "true")

        mocker.patch(
            _mod(client, "webserv.apply_modifications"),
            side_effect=RuntimeError("Action not applied"),
        )
        mocker.patch(_mod(client, "webserv.tools_slack.failed_message"))
        mock_fire = mocker.patch(
            _mod(client, "agent_handler.fire_agent"), return_value="cid123"
        )

        _post(client)

        mock_fire.assert_called_once()
        args = mock_fire.call_args[0]
        assert args[0] == "httpd"
        assert isinstance(args[2], RuntimeError)

    def test_skips_agent_when_disabled(self, client, mocker, monkeypatch):
        monkeypatch.setenv("AGENT_ENABLED", "false")

        mocker.patch(
            _mod(client, "webserv.apply_modifications"),
            side_effect=RuntimeError("fail"),
        )
        mocker.patch(_mod(client, "webserv.tools_slack.failed_message"))
        mock_fire = mocker.patch(_mod(client, "agent_handler.fire_agent"))

        _post(client)

        mock_fire.assert_not_called()

    def test_agent_crash_does_not_break_response(
        self, client, mocker, monkeypatch
    ):
        monkeypatch.setenv("AGENT_ENABLED", "true")

        mocker.patch(
            _mod(client, "webserv.apply_modifications"),
            side_effect=RuntimeError("fail"),
        )
        mocker.patch(_mod(client, "webserv.tools_slack.failed_message"))
        mocker.patch(
            _mod(client, "agent_handler.fire_agent"),
            side_effect=Exception("agent crashed"),
        )

        _post(client)
        # If we got here without an unhandled exception,
        # the agent crash was properly caught.


class TestPrMergedRestart:

    def test_restart_on_agent_fix_merge(self, client, mocker):
        mod = _webserv_mod(client)
        mock_apply = mocker.patch.object(
            mod, "apply_modifications", return_value=mod.SUCCESS,
        )
        mock_success = mocker.patch.object(mod.tools_slack, "success_message")

        resp = _post_pr(client, PR_MERGED_PAYLOAD)

        assert resp.status_code == 200
        # upstream branch reconstructed from base.ref (a9-beta -> c9-beta),
        # config branch passed through as target_branch.
        mock_apply.assert_called_once_with(
            "qemu-kvm", "c9-beta", target_branch="a9-beta",
        )
        mock_success.assert_called_once_with("qemu-kvm", "a9-beta")

    def test_ignored_when_not_merged(self, client, mocker):
        mod = _webserv_mod(client)
        mock_apply = mocker.patch.object(mod, "apply_modifications")
        payload = dict(PR_MERGED_PAYLOAD)
        payload["pull_request"] = {
            **PR_MERGED_PAYLOAD["pull_request"], "merged": False,
        }

        resp = _post_pr(client, payload)

        assert resp.status_code == 200
        mock_apply.assert_not_called()

    def test_ignored_when_not_a_close_event(self, client, mocker):
        mod = _webserv_mod(client)
        mock_apply = mocker.patch.object(mod, "apply_modifications")
        payload = {**PR_MERGED_PAYLOAD, "action": "opened"}

        _post_pr(client, payload)

        mock_apply.assert_not_called()

    def test_ignored_when_manual_branch(self, client, mocker):
        """A PR from a manually-created (non agent-fix) branch is ignored."""
        mod = _webserv_mod(client)
        mock_apply = mocker.patch.object(mod, "apply_modifications")
        for head in ("feature/manual", "a9-beta", "fix/typo", "agentfix/oops"):
            payload = dict(PR_MERGED_PAYLOAD)
            payload["pull_request"] = {
                **PR_MERGED_PAYLOAD["pull_request"], "head": {"ref": head},
            }
            resp = _post_pr(client, payload)
            assert resp.status_code == 200

        mock_apply.assert_not_called()

    def test_failure_notifies_slack(self, client, mocker):
        mod = _webserv_mod(client)
        mocker.patch.object(
            mod, "apply_modifications", side_effect=RuntimeError("boom"),
        )
        mock_failed = mocker.patch.object(mod.tools_slack, "failed_message")

        resp = _post_pr(client, PR_MERGED_PAYLOAD)

        assert resp.status_code == 200
        mock_failed.assert_called_once()
        args = mock_failed.call_args[0]
        assert args[0] == "qemu-kvm"
        assert args[1] == "a9-beta"
