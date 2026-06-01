"""Shared branch name resolution utilities.

Used by both debranding.py and agent_orchestrator.py to map
webhook branches (c9, c9-beta) to autopatch config branches (a9).
"""

import re

# Prefix of the branches the agent pushes for its fixes (see
# agent_orchestrator._commit_and_push). Used to distinguish agent-generated
# fix PRs — which trigger an automatic build restart on merge — from
# manually-created branches/PRs, which are ignored.
AGENT_FIX_BRANCH_PREFIX = "agent-fix/"


def resolve_config_branch(branch: str, target_branch: str = "") -> str:
    """Map a CentOS/RHEL branch name to the AlmaLinux autopatch config branch.

    Examples:
        resolve_config_branch("c9")       -> "a9"
        resolve_config_branch("c9-beta")  -> "a9-beta"
        resolve_config_branch("c10s")     -> "a10s"

    If target_branch is provided, it is returned as-is (custom override).
    """
    if target_branch:
        return target_branch
    return branch.replace("c", "a", 1)


def resolve_upstream_branch(config_branch: str) -> str:
    """Map an AlmaLinux config branch back to its CentOS/RHEL upstream branch.

    This is the inverse of :func:`resolve_config_branch`. Used when restarting
    a build after a fix PR is merged: the webhook only tells us the config
    branch (the PR base, e.g. ``a9-beta``), but ``apply_modifications`` needs
    the upstream import branch to reset the rpms repo from.

    Examples:
        resolve_upstream_branch("a9")       -> "c9"
        resolve_upstream_branch("a9-beta")  -> "c9-beta"
        resolve_upstream_branch("a10s")     -> "c10s"
    """
    return config_branch.replace("a", "c", 1)


def strip_beta(branch: str) -> str:
    """Remove '-beta' suffix from a branch name.

    Used as a fallback when the beta branch doesn't exist in the repo.

    Examples:
        strip_beta("a9-beta") -> "a9"
        strip_beta("a9")      -> "a9"
    """
    return branch.replace("-beta", "")


def get_sibling_branches(config_branch: str) -> list[str]:
    """Return related branches that may already have a fix, ordered by priority.

    Stream branches (aNs) are checked first because they typically receive
    patches before release/beta branches.

    Examples:
        get_sibling_branches("a10")       -> ["a10s", "a10-beta"]
        get_sibling_branches("a10-beta")  -> ["a10s", "a10"]
        get_sibling_branches("a10s")      -> ["a10", "a10-beta"]
        get_sibling_branches("a9")        -> ["a9s", "a9-beta"]
        get_sibling_branches("a9-beta")   -> ["a9s", "a9"]
    """
    m = re.match(r"^(a\d+)(s)?(-beta)?$", config_branch)
    if not m:
        return []
    base = m.group(1)
    all_variants = [f"{base}s", base, f"{base}-beta"]
    return [b for b in all_variants if b != config_branch]
