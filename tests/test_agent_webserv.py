"""Tests for the webhook handlers in webserv.py.

The handlers only check that the package has a config and queue a
background job (debrand_job.enqueue); the job itself is tested in
test_debrand_job.py.

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

CONFIG_PUSH_PAYLOAD = {
    "ref": "refs/heads/a9-beta",
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


def _post_config_push(client, payload):
    """Send a config-pushed webhook with a valid Gitea HMAC signature."""
    body = json.dumps(payload).encode()
    sig = hmac.new(
        key=AUTH_KEY.encode(),
        msg=body,
        digestmod="SHA256",
    ).hexdigest()
    return client.post(
        "/autopatch_config_pushed",
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


IMPORT_TAG_PAYLOAD = {
    "repository": {"name": "httpd"},
    "ref": "refs/tags/imports/c9/httpd-2.4.62-4.el9",
}


@pytest.fixture
def queue(client, mocker):
    """Mock the config lookup (package configured) and the job launch."""
    mod = _webserv_mod(client)
    mocks = types.SimpleNamespace(
        find=mocker.patch.object(
            mod, "find_config_branch", return_value=("a9", ""),
        ),
        enqueue=mocker.patch.object(mod, "enqueue"),
        failed=mocker.patch.object(mod.tools_slack, "failed_message"),
    )
    return mocks


class TestUpstreamPush:

    def test_queues_job_for_import_tag(self, client, queue):
        resp = _post(client, IMPORT_TAG_PAYLOAD)

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["message"] == _webserv_mod(client).QUEUED
        queue.find.assert_called_once_with("httpd", "c9", "")
        queue.enqueue.assert_called_once_with(
            "httpd", "c9", target_branch="", report_branch="c9",
        )
        queue.failed.assert_not_called()

    def test_unconfigured_package_is_not_queued(self, client, queue):
        """A push of a package without a config answers at once and starts
        no job, so a mass import does not spawn a process per package."""
        queue.find.return_value = ("", "Package is not modified")

        resp = _post(client, IMPORT_TAG_PAYLOAD)

        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Package is not modified"
        queue.enqueue.assert_not_called()

    def test_modified_branch_push_is_skipped(self, client, queue):
        resp = _post(client, {
            "repository": {"name": "httpd"},
            "ref": "refs/tags/changed/a9/httpd-2.4.62-4.el9",
        })

        assert resp.get_json()["success"] is False
        queue.enqueue.assert_not_called()

    def test_enqueue_failure_is_reported(self, client, queue, mocker):
        queue.enqueue.side_effect = RuntimeError("fork failed")
        mock_fire = mocker.patch(_mod(client, "agent_handler.fire_agent"))

        resp = _post(client, IMPORT_TAG_PAYLOAD)

        assert resp.status_code == 200
        assert resp.get_json()["success"] is False
        queue.failed.assert_called_once_with("httpd", "c9", "fork failed")
        # Not a config problem: nothing for the agent to fix.
        mock_fire.assert_not_called()

    def test_bare_ref_payload_is_skipped(self, client, queue):
        """Gitea create/delete events send a bare ref, not refs/.../<branch>.

        Such a payload has no branch to debrand: it must be answered with a
        plain "nothing to sync" instead of failing the whole request.
        """
        resp = _post(
            client, {"repository": {"name": "httpd"}, "ref": "c10s"},
        )

        assert resp is not None
        assert resp.status_code == 200
        assert resp.get_json()["success"] is False
        queue.find.assert_not_called()
        queue.enqueue.assert_not_called()
        queue.failed.assert_not_called()

    def test_payload_failure_is_reported_not_raised(
        self, client, queue, mocker,
    ):
        """A crash before the payload is parsed must still reach Slack.

        repo_name/branch are only assigned inside the try block, so the
        except block used to raise UnboundLocalError and lose the report.
        """
        mod = _webserv_mod(client)
        mocker.patch.object(
            mod,
            "get_name_from_payload",
            side_effect=ValueError("malformed payload"),
        )

        resp = _post(client)

        assert resp is not None
        assert resp.status_code == 200
        assert resp.get_json()["success"] is False
        queue.failed.assert_called_once_with("", "", "malformed payload")
        queue.enqueue.assert_not_called()


class TestConfigPushRestart:

    def test_restart_on_config_branch_push(self, client, queue):
        resp = _post_config_push(client, CONFIG_PUSH_PAYLOAD)

        assert resp.status_code == 200
        assert resp.get_json()["message"] == _webserv_mod(client).QUEUED
        # upstream branch reconstructed from the pushed config branch
        # (a9-beta -> c9-beta), config branch passed through as target_branch.
        queue.find.assert_called_once_with("qemu-kvm", "c9-beta", "a9-beta")
        queue.enqueue.assert_called_once_with(
            "qemu-kvm", "c9-beta",
            target_branch="a9-beta", report_branch="a9-beta",
        )

    def test_unconfigured_branch_is_not_queued(self, client, queue):
        queue.find.return_value = ("", "Branch is not modified")

        resp = _post_config_push(client, CONFIG_PUSH_PAYLOAD)

        assert resp.get_json()["message"] == "Branch is not modified"
        queue.enqueue.assert_not_called()

    def test_ignored_when_branch_deleted(self, client, queue):
        payload = {**CONFIG_PUSH_PAYLOAD, "deleted": True}

        resp = _post_config_push(client, payload)

        assert resp.status_code == 200
        queue.enqueue.assert_not_called()

    def test_ignored_when_tag_push(self, client, queue):
        payload = {**CONFIG_PUSH_PAYLOAD, "ref": "refs/tags/changed/a9/x-1.0"}

        resp = _post_config_push(client, payload)

        assert resp.status_code == 200
        queue.enqueue.assert_not_called()

    def test_ignored_for_non_config_branches(self, client, queue):
        """Upstream import, agent-fix and feature branches are ignored."""
        for branch in (
            "c9",                              # upstream import branch
            "agent-fix/a9-beta-20260601",      # agent working branch
            "feature/manual",                  # feature branch
            "main",
        ):
            payload = {**CONFIG_PUSH_PAYLOAD, "ref": f"refs/heads/{branch}"}
            resp = _post_config_push(client, payload)
            assert resp.status_code == 200

        queue.enqueue.assert_not_called()

    def test_ignored_on_merge_between_config_branches(self, client, queue):
        """Forward-merging a config branch into another (a9-beta -> a9) must
        not retrigger a rebuild on the target branch."""
        payload = {
            **CONFIG_PUSH_PAYLOAD,
            "ref": "refs/heads/a9",
            "head_commit": {"message": "Merge branch 'a9-beta' into a9"},
        }

        resp = _post_config_push(client, payload)

        assert resp.status_code == 200
        queue.enqueue.assert_not_called()

    def test_ignored_on_pr_merge_between_config_branches(self, client, queue):
        payload = {
            **CONFIG_PUSH_PAYLOAD,
            "ref": "refs/heads/a9",
            "head_commit": {
                "message": (
                    "Merge pull request 'Forward port' (#42) "
                    "from a9-beta into a9"
                ),
            },
        }

        resp = _post_config_push(client, payload)

        assert resp.status_code == 200
        queue.enqueue.assert_not_called()

    def test_rebuilds_on_pr_merge_from_fork_branch_named_like_config(
        self, client, queue,
    ):
        """A fork's branch named after a config branch (ykohut/...:a10) is a
        contributor's fix, not a forward-merge, and must trigger a rebuild."""
        payload = {
            **CONFIG_PUSH_PAYLOAD,
            "ref": "refs/heads/a10",
            "head_commit": {
                "message": (
                    "Merge pull request 'Use systemd-sulogin-shell form' (#5) "
                    "from ykohut/autopatch-scap-security-guide:a10 into a10"
                ),
            },
        }

        resp = _post_config_push(client, payload)

        assert resp.status_code == 200
        queue.enqueue.assert_called_once_with(
            "qemu-kvm", "c10", target_branch="a10", report_branch="a10",
        )

    def test_rebuilds_on_merge_from_non_config_branch(self, client, queue):
        """A merge from an agent-fix branch into a config branch is a real fix
        landing and must still trigger a rebuild."""
        payload = {
            **CONFIG_PUSH_PAYLOAD,
            "head_commit": {
                "message": (
                    "Merge pull request 'fix' (#7) "
                    "from agent-fix/a9-beta-20260601 into a9-beta"
                ),
            },
        }

        resp = _post_config_push(client, payload)

        assert resp.status_code == 200
        queue.enqueue.assert_called_once_with(
            "qemu-kvm", "c9-beta",
            target_branch="a9-beta", report_branch="a9-beta",
        )

    def test_failure_notifies_slack(self, client, queue):
        queue.find.side_effect = RuntimeError("Gitea API is down")

        resp = _post_config_push(client, CONFIG_PUSH_PAYLOAD)

        assert resp.status_code == 200
        assert resp.get_json()["success"] is False
        queue.failed.assert_called_once_with(
            "qemu-kvm", "a9-beta", "Gitea API is down",
        )
        queue.enqueue.assert_not_called()


try:
    from autopatch.tools.webserv_tools import (
        get_branch_from_payload,
        get_merge_source_branch,
    )
except ModuleNotFoundError:
    from tools.webserv_tools import (
        get_branch_from_payload,
        get_merge_source_branch,
    )


class TestGetMergeSourceBranch:

    @pytest.mark.parametrize(
        "message, expected",
        [
            # plain git merge
            ("Merge branch 'a9-beta' into a9", "a9-beta"),
            # git merge into the default branch (no "into")
            ("Merge branch 'a9-beta'", "a9-beta"),
            # Gitea PR merge, same repo
            (
                "Merge pull request 'Title' (#1) from a9-beta into a9",
                "a9-beta",
            ),
            # Gitea PR merge from a fork: the owner/repo prefix is kept so a
            # fork branch named like a config branch is not taken for one
            (
                "Merge pull request 'Title' (#5) "
                "from ykohut/autopatch-scap-security-guide:a10 into a10",
                "ykohut/autopatch-scap-security-guide:a10",
            ),
            # Gitea PR merge from a fork that was deleted since
            (
                "Merge pull request 'Title' (#5) from <deleted>:a10 into a10",
                "<deleted>:a10",
            ),
            # PR merge from an agent-fix branch
            (
                "Merge pull request 'fix' (#7) "
                "from agent-fix/a9-beta-20260601 into a9-beta",
                "agent-fix/a9-beta-20260601",
            ),
            # title containing the word "from" must not confuse extraction
            (
                "Merge pull request 'Backport from upstream' (#9) "
                "from a9s into a9",
                "a9s",
            ),
            # not a merge -> no source
            ("Fix CVE-2026-1234 in spec", ""),
            # multi-line message: only the subject line is parsed
            ("Merge branch 'a9-beta' into a9\n\nDetails here", "a9-beta"),
        ],
    )
    def test_extracts_source_branch(self, message, expected):
        payload = {"head_commit": {"message": message}}
        assert get_merge_source_branch(payload) == expected

    def test_missing_head_commit_returns_empty(self):
        assert get_merge_source_branch({}) == ""
        assert get_merge_source_branch({"head_commit": None}) == ""
        assert get_merge_source_branch({"head_commit": {}}) == ""


class TestGetBranchFromPayload:

    @pytest.mark.parametrize(
        "ref, expected",
        [
            # upstream import tag -- the ref debranding actually runs on
            ("refs/tags/imports/c10s/kernel-6.12.0-211.el10", "c10s"),
            ("refs/tags/imports/c9/httpd-2.4.62-4.el9", "c9"),
            # branch push
            ("refs/heads/c9", "heads"),
            # bare name, as sent by Gitea create/delete events -> skipped
            ("c10s", ""),
            ("", ""),
        ],
    )
    def test_extracts_branch(self, ref, expected):
        assert get_branch_from_payload({"ref": ref}) == expected

    def test_missing_or_null_ref_returns_empty(self):
        assert get_branch_from_payload({}) == ""
        assert get_branch_from_payload({"ref": None}) == ""
