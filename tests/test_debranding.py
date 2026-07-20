"""Tests for working-directory isolation in debranding.apply_modifications.

apply_modifications must run each debranding in its own unique working
directory so that concurrent runs of the same package -- e.g. two gunicorn
workers handling pushes to ``a10`` and ``a10-beta`` -- never share a clone
path and race on it (which made git fail with "No such file or directory"
while cloning the large kernel repo). It must also always remove that
directory afterwards, on success and on failure alike, so repeated runs do
not leak full clones onto disk.

debranding has a deep import chain (debranding -> tools.git ->
immudb_wrapper); we stub the notarization module and monkeypatch every
collaborator so the tests touch no network, git, or rpm tooling.
"""

import os
import sys
import tempfile
import types
from unittest.mock import MagicMock

import pytest


_STUB_MODULES = ["immudb_wrapper", "immudb", "immudb.client"]


@pytest.fixture
def deb(monkeypatch, tmp_path):
    monkeypatch.setenv("ALLOW_NOTARIZATION", "false")

    for mod_name in _STUB_MODULES:
        if mod_name not in sys.modules:
            monkeypatch.setitem(sys.modules, mod_name, types.ModuleType(mod_name))

    try:
        from autopatch import debranding as module
    except ModuleNotFoundError:
        import debranding as module

    # Run inside an isolated cwd: the per-run working root is created under
    # os.getcwd(), so this keeps any stray directory inside tmp_path.
    monkeypatch.chdir(tmp_path)

    # Stub every collaborator so nothing reaches the network / git / rpm.
    monkeypatch.setattr(module, "resolve_config_branch", lambda branch, target: branch)
    monkeypatch.setattr(module, "strip_beta", lambda branch: branch)
    monkeypatch.setattr(module, "extract_el_version", lambda branch: 10)
    monkeypatch.setattr(module, "get_config_files", lambda path, package: ["config.yaml"])

    galma = MagicMock()
    galma.ALMALINUX_GIT = "git.almalinux.org"
    galma.AUTOPATCH_NAMESPACE = "autopatch"
    galma.RPMS_NAMESPACE = "rpms"
    galma.get_list_of_modified_packages.return_value = ["kernel"]
    galma.get_branches_from_package.return_value = ["a10"]
    monkeypatch.setattr(module, "GitAlmaLinux", galma)

    git_repo = MagicMock()
    monkeypatch.setattr(module, "GitRepository", MagicMock(return_value=git_repo))

    config = MagicMock()
    config.global_parameters.custom_target_branch = ""
    config.global_parameters.tag_prefix = ""
    config.global_parameters.pre_clean = False
    config.get_release_suffix.return_value = ""
    config.get_changelog.return_value = (["changelog entry"], "Name", "e@x.org")
    monkeypatch.setattr(module, "ConfigReader", lambda *a, **k: config)

    # DirectoryManager is a no-op context manager here: we neither chdir nor
    # create/clone anything, so the only directory on disk is the run root
    # created by apply_modifications itself.
    class _NoopDirectoryManager:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(module, "DirectoryManager", _NoopDirectoryManager)

    # Spy on mkdtemp to capture every per-run working root that is created.
    created_roots = []
    real_mkdtemp = tempfile.mkdtemp

    def _spy_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created_roots.append(path)
        return path

    monkeypatch.setattr(module, "tempfile", types.SimpleNamespace(mkdtemp=_spy_mkdtemp))

    return types.SimpleNamespace(
        module=module,
        created_roots=created_roots,
        git_repo=git_repo,
        config=config,
        tmp_path=tmp_path,
    )


def test_creates_and_cleans_isolated_working_dir(deb):
    result = deb.module.apply_modifications("kernel", "a10")

    assert result == deb.module.SUCCESS
    assert len(deb.created_roots) == 1

    run_root = deb.created_roots[0]
    # Created under the current working directory, package-scoped prefix.
    assert os.path.realpath(os.path.dirname(run_root)) == os.path.realpath(str(deb.tmp_path))
    assert os.path.basename(run_root).startswith("autopatch-kernel-")
    # Removed afterwards -> no leaked clone left behind.
    assert not os.path.exists(run_root)
    assert os.listdir(deb.tmp_path) == []


def test_concurrent_runs_get_distinct_working_dirs(deb):
    deb.module.apply_modifications("kernel", "a10")
    deb.module.apply_modifications("kernel", "a10")

    # Each run gets its own root: no shared fixed path for concurrent runs of
    # the same package to race on.
    assert len(deb.created_roots) == 2
    assert deb.created_roots[0] != deb.created_roots[1]


def test_working_dir_removed_on_failure(deb):
    deb.git_repo.push.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        deb.module.apply_modifications("kernel", "a10")

    # The failure must not leave the (potentially gigabytes) clone on disk.
    assert len(deb.created_roots) == 1
    assert not os.path.exists(deb.created_roots[0])
    assert os.listdir(deb.tmp_path) == []


def test_no_working_dir_for_unmodified_package(deb):
    # The cheap "is this package modified?" check runs before any working
    # directory is created, so the many no-op webhook deliveries never churn
    # temp dirs.
    deb.module.GitAlmaLinux.get_list_of_modified_packages.return_value = []

    result = deb.module.apply_modifications("kernel", "a10")

    assert result == deb.module.PACKAGE_NOT_MODIFIED
    assert deb.created_roots == []
    assert os.listdir(deb.tmp_path) == []
