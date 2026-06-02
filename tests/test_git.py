import re
import textwrap
from subprocess import run, PIPE
import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from src.tools.git import GitRepository, DirectoryManager
from src.actions_handler import ConfigReader


@pytest.fixture
def temp_git_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd=repo_path, check=True)
        yield repo_path


def get_current_branch(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def test_directory_manager_success(tmp_path):
    new_dir = tmp_path / "new_test_directory"

    previous_path = Path.cwd()

    with DirectoryManager(new_dir):
        assert Path.cwd() == new_dir

    assert Path.cwd() == previous_path


def test_directory_manager_existing_directory(tmp_path):
    existing_dir = tmp_path / "existing_directory"
    existing_dir.mkdir()

    with DirectoryManager(existing_dir):
        assert Path.cwd() == existing_dir

def test_directory_manager_failure(mocker):
    mocker.patch("os.chdir", side_effect=OSError("Read-only file system"))

    with pytest.raises(OSError, match="Read-only file system"):
        with DirectoryManager("/unavailable_directory"):
            pass

def test_directory_manager_logging_success(mocker, tmp_path):
    mock_logger = mocker.patch("src.tools.git.logger")
    new_dir = tmp_path / "logging_directory"

    with DirectoryManager(new_dir):
        pass

    mock_logger.debug.assert_any_call(f"Switching to directory {new_dir}")
    mock_logger.debug.assert_any_call(f"Reverting to directory {Path.cwd()}")

def test_directory_manager_logging_error(mocker):
    mock_logger = mocker.patch("src.tools.git.logger")
    mocker.patch("os.chdir", side_effect=OSError("Read-only file system"))

    with pytest.raises(OSError):
        with DirectoryManager("/invalid_path"):
            pass

    mock_logger.error.assert_any_call("Error changing directory: Read-only file system", )

def test_directory_manager_creates_parents(tmp_path):
    nested_dir = tmp_path / "parent/child/grandchild"

    with DirectoryManager(nested_dir):
        assert nested_dir.exists()



def test_create_tag_without_prefix(temp_git_repo):
    repo = GitRepository(str(temp_git_repo), clone=False, local_repo=True)
    repo.create_tag("v1.0.0")
    result = subprocess.run(
        ["git", "tag", "--list"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "v1.0.0" in result.stdout.splitlines()

def test_create_tag_with_prefix(temp_git_repo):
    repo = GitRepository(str(temp_git_repo), clone=False, local_repo=True)
    repo.create_tag("v1.0.0", prefix="release/")
    result = subprocess.run(
        ["git", "tag", "--list"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    tags = result.stdout.splitlines()
    assert "release/v1.0.0" in tags
    assert "v1.0.0" not in tags

def test_create_tag_with_empty_prefix(temp_git_repo):
    repo = GitRepository(str(temp_git_repo), clone=False, local_repo=True)
    repo.create_tag("v2.0.0", prefix="")
    result = subprocess.run(
        ["git", "tag", "--list"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "v2.0.0" in result.stdout.splitlines()


def test_list_tags_returns_all_and_filters(temp_git_repo):
    repo = GitRepository(str(temp_git_repo), clone=False, local_repo=True)
    tags = [
        "changed/a9/pkg-1.0-1.el9.alma.1",
        "changed/a9/pkg-1.0-1.el9.alma.2",
        "imports/c9/pkg-1.0-1.el9",
    ]
    for tag in tags:
        repo.create_tag(tag)

    assert set(repo.list_tags()) == set(tags)

    filtered = repo.list_tags("changed/a9/*")
    assert set(filtered) == {
        "changed/a9/pkg-1.0-1.el9.alma.1",
        "changed/a9/pkg-1.0-1.el9.alma.2",
    }


def test_list_tags_empty(temp_git_repo):
    repo = GitRepository(str(temp_git_repo), clone=False, local_repo=True)
    assert repo.list_tags() == []


def test_list_tags_includes_unreachable_tags(temp_git_repo):
    # The reason list_tags uses `git tag --list` instead of `git describe` is
    # that the autopatch flow is checked out on the upstream import branch (c9)
    # while the `changed/*` tags live on the autopatch branch (a9), unreachable
    # from HEAD. `git describe` would not see them; `git tag --list` must.
    base_branch = get_current_branch(temp_git_repo)

    subprocess.run(["git", "checkout", "-b", "sidebranch"], cwd=temp_git_repo, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "side commit"],
        cwd=temp_git_repo, check=True,
    )
    subprocess.run(
        ["git", "tag", "changed/a9/pkg-1.0-1.el9.alma.5"],
        cwd=temp_git_repo, check=True,
    )
    subprocess.run(["git", "checkout", base_branch], cwd=temp_git_repo, check=True)

    repo = GitRepository(str(temp_git_repo), clone=False, local_repo=True)
    assert "changed/a9/pkg-1.0-1.el9.alma.5" in repo.list_tags()


def test_auto_increment_release_drives_spec_and_tag(temp_git_repo, tmp_path):
    """End-to-end: existing git tags drive both the bumped tag suffix and the
    spec Release line, the way debranding.apply_modifications wires them."""
    base_tag = "changed/a9/pkg-1.0-1.el9"

    repo = GitRepository(str(temp_git_repo), clone=False, local_repo=True)
    repo.create_tag(f"{base_tag}.alma.1")
    repo.create_tag(f"{base_tag}.alma.2")
    repo.create_tag("imports/c9/pkg-1.0-1.el9")  # must be ignored

    config_file = tmp_path / "config.yaml"
    config_file.write_text(textwrap.dedent("""
        actions:
          - modify_release:
            - suffix: ".alma.1"
              auto_increment: true
    """))
    config = ConfigReader(config_file)

    config.resolve_release_iteration(
        existing_tags=repo.list_tags(),
        base_tag=base_tag,
        tag_prefix="",
    )

    # 1) The git tag suffix is bumped to the next iteration.
    assert config.get_release_suffix() == ".alma.3"
    assert base_tag + config.get_release_suffix() == f"{base_tag}.alma.3"

    # 2) The same suffix is applied to the spec Release line.
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    spec = pkg_dir / "pkg.spec"
    spec.write_text(
        "Name: pkg\nVersion: 1.0\nRelease: 1%{?dist}\n\n%description\nx\n\n%changelog\n"
    )
    config.apply_actions(pkg_dir)

    assert "Release: 1%{?dist}.alma.3" in spec.read_text()


def test_auto_increment_release_resets_on_new_version(temp_git_repo, tmp_path):
    """A new upstream version (different base_tag) has no matching tags, so the
    iteration falls back to the configured starting number."""
    repo = GitRepository(str(temp_git_repo), clone=False, local_repo=True)
    # Tags exist only for the OLD version.
    repo.create_tag("changed/a9/pkg-1.0-1.el9.alma.4")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(textwrap.dedent("""
        actions:
          - modify_release:
            - suffix: ".alma.1"
              auto_increment: true
    """))
    config = ConfigReader(config_file)

    config.resolve_release_iteration(
        existing_tags=repo.list_tags(),
        base_tag="changed/a9/pkg-2.0-1.el9",  # NEW version
        tag_prefix="",
    )

    assert config.get_release_suffix() == ".alma.1"


def test_clone_real_repository():
    tmpdir = Path("tmpdir")
    repo_path = tmpdir / "test_repo"
    git_url = "https://git.almalinux.org/rpms/test_repo.git"

    with DirectoryManager(str(tmpdir)):
        repo = GitRepository(git_url)

    assert repo_path.exists()
    assert (repo_path / ".git").exists()

    shutil.rmtree(tmpdir)


def test_git_checkout_existing_branch():
    git_url = "https://git.almalinux.org/rpms/test_repo.git"
    repo = GitRepository(git_url)

    branch_to_checkout = "a8"  # Существующая ветка
    repo.checkout_branch(branch_to_checkout)
    current_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd="test_repo",
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert current_branch == branch_to_checkout

def test_git_commit():
    git_url = "https://git.almalinux.org/rpms/test_repo.git"
    repo = GitRepository(git_url)

    # Создаем файл и коммитим его
    new_file = Path("test_repo/new_file.txt")
    new_file.write_text("Test content")
    repo.commit(["Add new_file.txt"], "test", "test@test.test")

    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd="test_repo",
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Add new_file.txt" in result.stdout

def test_git_reset_to_base_branch():
    git_url = "https://git.almalinux.org/rpms/test_repo.git"
    repo = GitRepository(git_url)

    repo.checkout_branch("a8")
    run(["git", "pull"], cwd="test_repo", check=True)

    repo.checkout_branch("c8")
    run(["git", "pull"], cwd="test_repo", check=True)

    repo.checkout_branch("c8")
    c8_spec_content = (Path("test_repo/libdnf.spec").read_text()).strip()

    repo.reset_to_base_branch("c8", "a8")

    a8_spec_content = (Path("test_repo/libdnf.spec").read_text()).strip()

    assert a8_spec_content == c8_spec_content, "Files libdnf.spec do not match"

    repo.checkout_branch("a8")
    log_output = run(
        ["git", "log", "--oneline"],
        cwd="test_repo",
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        check=True
    ).stdout

    expected_commits = [
        "Merge 'c8' into 'a8'",
        "Add not removable line",
        "Update spec",
        "Test commit 1",
        "Initial commit",
        "Test commit"
    ]

    actual_commits = [re.sub(r'^[a-f0-9]{7,} ', '', line) for line in log_output.splitlines()]

    assert actual_commits[:len(expected_commits)] == expected_commits, "History of commits is incorrect"
    shutil.rmtree("test_repo")
