import os
import shutil
import tempfile

# First try importing via site-packages path, then try directly from "src"
try:
    from autopatch.tools.logger import logger
    from autopatch.actions_handler import ConfigReader
    from autopatch.tools.git import GitRepository, GitAlmaLinux, DirectoryManager
    from autopatch.tools.rpm import extract_el_version
    from autopatch.tools.branch import resolve_config_branch, strip_beta
except ImportError:
    from tools.logger import logger
    from actions_handler import ConfigReader
    from tools.git import GitRepository, GitAlmaLinux, DirectoryManager
    from tools.rpm import extract_el_version
    from tools.branch import resolve_config_branch, strip_beta

BRANCH_NOT_MODIFIED = "Branch is not modified"
PACKAGE_NOT_MODIFIED = "Package is not modified"
SUCCESS = "Debranding applied"


def get_config_files(autopatch_path: str, package: str) -> list[str]:
    config_files = []
    for file in os.listdir(autopatch_path + f"/{package}"):
        if file.endswith(".yaml") and file.startswith("config"):
            config_files.append(file)
    return config_files


def apply_modifications(
    package,
    branch,
    set_custom_tag: str = "",
    no_tag: bool = False,
    target_branch: str = "",
):
    config_branch = al_branch = resolve_config_branch(branch, target_branch)

    if package not in GitAlmaLinux.get_list_of_modified_packages():
        logger.info(f"Package {package} is not modified")
        return PACKAGE_NOT_MODIFIED

    config_branches = GitAlmaLinux.get_branches_from_package(package)

    if config_branch not in config_branches and '-beta' in config_branch:
        config_branch = strip_beta(al_branch)

    if config_branch not in config_branches:
        logger.info(f"Branch {al_branch} does not exist")
        return BRANCH_NOT_MODIFIED

    # Isolate every run in its own working directory. Debranding of a single
    # package can run concurrently -- e.g. separate gunicorn workers handling a
    # push to both `a10` and `a10-beta` -- and each run clones into
    # `<root>/autopatch-namespace/<package>` and `<root>/rpms-namespace/<package>`.
    # With a shared root those clones collide: GitRepository re-clones by first
    # removing any existing directory (shutil.rmtree), which yanks the pack
    # files out from under a clone still running in the other worker and makes
    # git fail with "No such file or directory". A unique root per run removes
    # the shared path entirely. It is created under the current working
    # directory so clones stay on the same filesystem as before (large repos
    # such as the kernel must not spill onto a possibly small /tmp).
    run_root = tempfile.mkdtemp(prefix=f"autopatch-{package}-", dir=os.getcwd())
    autopatch_working_dir = os.path.join(run_root, "autopatch-namespace")
    rpms_working_dir = os.path.join(run_root, "rpms-namespace")

    try:
        with DirectoryManager(autopatch_working_dir):
            config_repo = GitRepository(
                f"git@{GitAlmaLinux.ALMALINUX_GIT}:{GitAlmaLinux.AUTOPATCH_NAMESPACE}/{package}.git"
            )
            config_repo.checkout_branch(config_branch)
            config_repo.pull()

        el_version = extract_el_version(branch)
        logger.info(f"Detected EL version: {el_version} (from branch '{branch}')")

        config_files = get_config_files(autopatch_working_dir, package)
        if not config_files:
            logger.warning(f"No config files found for package {package}")
            raise RuntimeError(f"No config files found for package {package}")

        any_committed = False

        for config_file in config_files:
            logger.info(f"Processing config file {config_file}")
            _al_branch = al_branch

            config = ConfigReader(
                f"{autopatch_working_dir}/{package}/{config_file}",
                el_version=el_version
            )
            if config.global_parameters.custom_target_branch:
                _al_branch = config.global_parameters.custom_target_branch

            if config_file != "config.yaml" and _al_branch == al_branch:
                message = (
                    f"Additional config {config_file} exists,"
                    "but custom_target_branch is not specified in the config file's global parameters"
                )
                logger.warning(message)
                raise RuntimeError(message)

            with DirectoryManager(rpms_working_dir):
                git_repo = GitRepository(
                    f"git@{GitAlmaLinux.ALMALINUX_GIT}:{GitAlmaLinux.RPMS_NAMESPACE}/{package}.git"
                )
                git_repo.checkout_branch(branch)
                if not set_custom_tag:
                    base_tag = git_repo.get_latest_tag().replace(
                        f"imports/{branch}",
                        f"changed/{_al_branch}",
                        1
                    )
                    # Resolve auto-incrementing release suffixes (.alma.N) against
                    # tags already present in the repo. Must run before both the tag
                    # is built below and apply_actions() rewrites the spec Release,
                    # so the spec and the tag share the same iteration number.
                    config.resolve_release_iteration(
                        existing_tags=git_repo.list_tags(),
                        base_tag=base_tag,
                        tag_prefix=config.global_parameters.tag_prefix,
                    )
                    tag = base_tag + config.get_release_suffix()
                else:
                    tag = set_custom_tag
                git_repo.pull()
                upstream_hash = git_repo.get_sbom_hash()

                git_repo.reset_to_base_branch(
                    branch,
                    _al_branch,
                    no_commit=True,
                    pre_clean=config.global_parameters.pre_clean
                )
                config.apply_actions(rpms_working_dir + f"/{package}")

                changelog_entries, name, email = config.get_changelog()

                if not git_repo.commit(changelog_entries, name, email):
                    # Debranding produced no change relative to the target
                    # branch -- e.g. the package is already debranded for the
                    # current upstream state. There is nothing to tag, push or
                    # notarize: a no-op run, not a failure.
                    logger.info(
                        f"No changes for {package} on branch {_al_branch}; "
                        "already up to date"
                    )
                    continue

                any_committed = True
                if not no_tag:
                    git_repo.create_tag(tag, prefix=config.global_parameters.tag_prefix)
                git_repo.push(_al_branch)
                git_repo.notarize_commit(upstream_hash)

        return SUCCESS if any_committed else BRANCH_NOT_MODIFIED
    finally:
        # Always remove the isolated working tree. A fresh clone is made on
        # every run, so nothing here is reused; keeping it would leak a full
        # clone (potentially gigabytes, e.g. the kernel) per invocation.
        # ignore_errors keeps cleanup from masking the real result or error.
        shutil.rmtree(run_root, ignore_errors=True)
