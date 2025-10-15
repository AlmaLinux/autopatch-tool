import re
from subprocess import run, PIPE
import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from src.tools.git import GitRepository, DirectoryManager


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
