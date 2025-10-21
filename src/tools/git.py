import shutil
import os
import requests
from pathlib import Path


# First try importing via site-packages path, then try directly from "src"
try:
    from autopatch.tools.logger import logger
    from autopatch.tools.tools import (
        run_command,
        load_cas_credentials,
    )
except ImportError:
    from tools.logger import logger
    from tools.tools import (
        run_command,
        load_cas_credentials,
    )

ALLOW_NOTARIZATION = os.getenv("ALLOW_NOTARIZATION", "true").lower() == "true"
if ALLOW_NOTARIZATION:
    from immudb_wrapper import ImmudbWrapper

class DirectoryManager:
    """
    Context manager for changing the current working directory
    """
    def __init__(self, path):
        self.new_path = Path(path)
        self.previous_path = Path.cwd()

    def __enter__(self):
        try:
            self.new_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Switching to directory {self.new_path}")
            os.chdir(self.new_path)
        except Exception as e:
            logger.error(f"Error changing directory: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug(f"Reverting to directory {self.previous_path}")
        os.chdir(self.previous_path)

class GitRepositoryError(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class GitRepository:
    # pylint: disable=missing-function-docstring
    """
    Class for working with git repositories
    """
    def __init__(self, url, clone: bool = True, local_repo: bool = False):
        """
        Initialize the GitRepository instance.
        :param url: URL of the git repository
        :param clone: Whether to clone the repository if it does not exist locally
        :param local_repo: If True, treat the URL as a local path instead of a remote URL..
        """
        self.name = self.url = url

        if not local_repo:
            self.name = self.url.split("/")[-1].replace(".git", "")

        if ALLOW_NOTARIZATION:
            self.immudb_wrapper = ImmudbWrapper(**load_cas_credentials())

        if clone and not local_repo:
            self.__clone()

    def __clone(self):
        logger.info(f"Cloning repository {self.url}")
        if Path(self.name).exists():
            shutil.rmtree(self.name)
        run_command(["git", "clone", self.url])

    def run_in_repo(self, *command, shell=False):
        with DirectoryManager(self.name):
            run_command(list(command), shell=shell)

    def pull(self):
        logger.info(f"Pulling repository {self.url}")
        self.run_in_repo("git", "pull")

    def pull_branch(self, branch: str):
        logger.info(f"Pulling repository {self.url} branch {branch}")
        self.run_in_repo("git", "pull", "origin", branch)

    def create_tag(self, tag: str, prefix: str = ""):
        logger.info(f"Creating tag {prefix}{tag}")
        self.run_in_repo("git", "tag", f"{prefix}{tag}")

    def push_tags(self):
        logger.info(f"Pushing tag new tags to {self.name}")
        self.run_in_repo("git", "push", "--tags")

    def push(self, branch: str, force: bool = False):
        logger.info(f"Pushing to repository {self.url}")
        command = ["git", "push", "origin", branch]
        if force:
            command.append("-f")
        self.run_in_repo(*command)
        self.push_tags()

    def commit(self, message: list, name: str, email: str):
        logger.info(f"Committing changes to {self.url}")
        commit_messages = []
        for line in message:
            commit_messages.extend(["-m", line])
        self.run_in_repo("git", "add", ".")
        self.run_in_repo("git", "commit", "--author", f'"{name} <{email}>"', *commit_messages)

    def checkout_branch(self, branch: str):
        logger.info(f"Checking out branch {branch}")
        with DirectoryManager(self.name):
            result = run_command(["git", "checkout", branch], raise_on_failure=False)
            if result.returncode != 0:
                logger.info(f"Branch {branch} does not exist, creating it.")
                run_command(["git", "checkout", "--orphan", branch])

    def replace_file(self, replacing_branch: str, file: str):
        """
        Replace a file with the contents of another branch.
        """
        logger.info(f"Replacing file {file} with {replacing_branch}")
        self.run_in_repo("git", "checkout", replacing_branch, "--", file)

    def get_sbom_hash(self) -> str:
        """
        Get the SBOM hash of the current commit.
        """
        if not ALLOW_NOTARIZATION:
            return ""
        try:
            result = self.immudb_wrapper.authenticate_git_repo(self.name)
            matching_tag_is_authenticated = result.get('verified', False)

            if not matching_tag_is_authenticated:
                logger.error(f"Upstream commit is not notarized")
                raise GitRepositoryError("Upstream commit is not notarized")
            matching_immudb_hash = result.get('value', {}).get('Hash')

            logger.info(f"Upstream commit is notarized with hash: {matching_immudb_hash}")
        except Exception as e:
            logger.error(f"Failed to authenticate git repo: {e}")
            raise GitRepositoryError(f"Failed to authenticate git repo: {e}")

        return matching_immudb_hash

    def notarize_commit(self, upstream_hash: str = None) -> str:
        if not ALLOW_NOTARIZATION:
            return ""
        response = self.immudb_wrapper.notarize_git_repo(
            self.name,
            user_metadata={'sbom_api_ver': '0.2', 'upstream_commit_sbom_hash': upstream_hash},
        )
        if response.get('verified') != True:
            logger.error(f"Failed to notarize commit: {response}")
            raise GitRepositoryError("Failed to notarize commit")
        hash = response.get('value', {}).get('Hash')
        logger.info(f"Commit notarization hash: {hash}")

        return hash

    def merge_branch(self, branch: str, strategy: str = None, no_commit: bool = False):
        command = ["git", "merge", branch, "--no-edit"]

        if 'ours' not in strategy and 'theirs' not in strategy:
            logger.error(f"Invalid strategy: {strategy}")
            raise GitRepositoryError("Invalid strategy")

        if strategy:
            command.extend(["-X", strategy])
        if no_commit:
            command.append("--no-commit")

        logger.debug(f"Merging branch {branch} with options: strategy={strategy}, no_commit={no_commit}")
        self.run_in_repo(*command)

    def clean_repodir(self):
        with DirectoryManager(self.name):
            if os.path.exists('.'):
                for item in os.listdir('.'):
                    if item.startswith('.'):
                        logger.debug(f"Skipping hidden file: {item}")
                        continue
                    item_path = os.path.join('.', item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                        logger.debug(f"Deleted file: {item_path}")
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        logger.debug(f"Deleted folder: {item_path}")
            else:
                logger.error(f"Directory is empty: {self.name}")

    def reset_to_base_branch(self, base_branch: str, target_branch: str, no_commit: bool = False, pre_clean: bool = False):
        self.checkout_branch(base_branch)
        self.checkout_branch(target_branch)

        if pre_clean:
            logger.info(f"Pre-cleaning target branch {target_branch} before merging {base_branch}")
            self.clean_repodir()
            self.replace_file(base_branch, '.')

        try:
            self.merge_branch(base_branch, strategy='theirs', no_commit=True)
        except RuntimeError as e:
            if pre_clean: # in case of pre-clean, we just ignore the error
                logger.info(f"Failed to merge branch {base_branch} into {target_branch} with pre-clean: {e}")
            else:
                logger.error(f"Failed to merge branch {base_branch} into {target_branch}: {e}")
                raise e
        # All files in the target branch should be replaced with the files in the base branch
        self.clean_repodir()
        self.replace_file(base_branch, '.')

        if not no_commit:
            self.commit(
                [f"Merge '{base_branch}' into '{target_branch}'"],
                "AlmaLinux Autopatch",
                ""
            )

    def get_latest_tag(self):
        with DirectoryManager(self.name):
            return run_command(["git", "describe", "--tags", "--abbrev=0"]).stdout.strip()


class GitAlmaLinux:
    """
    Class for working with AlmaLinux git autopatch namespace
    """
    ALMALINUX_GIT = 'git.almalinux.org'
    ALMALINUX_GIT_URL = f'https://{ALMALINUX_GIT}'
    ALMALINUX_GIT_API = f'https://{ALMALINUX_GIT}/api/v1'  # https://git.almalinux.org/api/v1
    AUTOPATCH_NAMESPACE = 'autopatch'
    RPMS_NAMESPACE = 'rpms'

    @staticmethod
    def _iterate_over_pages(url):
        all_results = []
        page = 1

        with requests.Session() as session:
            while True:
                full_url = f"{url}?page={page}&limit=30"
                response = session.get(full_url, timeout=10)

                if response.status_code != 200:
                    logger.error(f"Failed to get data from {full_url} with status code {response.status_code}:\n{response.text}")
                    raise requests.HTTPError(
                        f"Failed to get data from {full_url}: {response.status_code}"
                    )

                data = response.json()
                if not data:
                    break

                all_results.extend(data)
                page += 1

        return all_results

    @staticmethod
    def get_list_of_modified_packages():
        """
        Get the list of modified packages.
        """
        url = f"{GitAlmaLinux.ALMALINUX_GIT_API}/orgs/{GitAlmaLinux.AUTOPATCH_NAMESPACE}/repos"
        repos = GitAlmaLinux._iterate_over_pages(url)

        return [repo['name'] for repo in repos if not repo['archived']]

    @staticmethod
    def get_branches_from_package(package_name):
        """
        Get the list of branches from a package.
        """
        url = (f"{GitAlmaLinux.ALMALINUX_GIT_API}/repos/"
               f"{GitAlmaLinux.AUTOPATCH_NAMESPACE}/{package_name}/branches")
        branches = GitAlmaLinux._iterate_over_pages(url)

        return [branch['name'] for branch in branches]
