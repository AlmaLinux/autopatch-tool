from __future__ import annotations

import os
import yaml
from slack_sdk.web import WebClient


CHAT_NAME = 'almalinux-debranding'

def get_slack_token(
    path: str = '~/.almalinux-debranding-slack/token'
) -> str:
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content['token']
    except OSError:
        return

client = WebClient(get_slack_token())

def failed_message(package_name:str, branch: str, error: str):
    message = f"Failed to debrand package `{package_name}` on branch `{branch}`:\n```{error}```"
    client.chat_postMessage(
        channel=CHAT_NAME,
        text=message
    )

def success_message(package_name:str, branch: str):
    message = f"Successfully debranded package `{package_name}` on branch `{branch}`\n"
    client.chat_postMessage(
        channel=CHAT_NAME,
        text=message
    )

def agent_auth_failed_message(
    auth_volume: str,
    image: str,
    package: str | None = None,
    branch: str | None = None,
    token_file: str | None = None,
):
    """Report that the agent's Claude Code credentials no longer work.

    Kept separate from agent_result_message() because this is not one package
    failing to be fixed — it blocks every further agent run until a human
    re-authenticates, so the message always spells out how.

    token_file is set when the agent authenticates with a `claude setup-token`
    token; renewing that is a different procedure from re-logging into the
    stored session, so the instructions must not be generic.
    """
    if package and branch:
        header = (
            f"Autopatch agent could not authenticate, so `{package}` on "
            f"`{branch}` was left unfixed."
        )
    else:
        header = "Autopatch agent could not authenticate."

    if token_file:
        how_to_fix = (
            "The long-lived Claude Code token is no longer valid, and every "
            "agent run will fail until it is renewed. Generate a new one on a "
            "workstation with a Claude subscription:\n"
            "```claude setup-token```\n"
            "then put it into the vaulted `claude_code_oauth_token` and "
            "re-deploy (or write it to "
            f"`{token_file}` on the host and restart "
            "`almalinux-autopatch.service`)."
        )
    else:
        how_to_fix = (
            "The stored Claude Code session is no longer valid, and every agent "
            "run will fail until it is renewed. On the autopatch host run:\n"
            f"```podman run -it -v {auth_volume}:/home/agent/.claude "
            f"--entrypoint claude {image} login```"
        )

    message = f"{header}\n{how_to_fix}"
    client.chat_postMessage(
        channel=CHAT_NAME,
        text=message
    )

def agent_result_message(
    package: str,
    branch: str,
    success: bool,
    summary: str,
    branch_name: str | None = None,
    dry_run: bool = False,
    config_branch: str | None = None,
    pr_url: str | None = None,
    pr_blocked: str | None = None,
):
    target = config_branch or branch
    if success and branch_name and pr_blocked:
        message = (
            f"Agent fixed `{package}` on `{branch}` and pushed branch `{branch_name}`, "
            f"but could NOT create the PR target branch `{pr_blocked}` — PR was not opened "
            f"to avoid merging into the wrong branch.\n"
            f"Please create `{pr_blocked}` and open the PR manually."
        )
    elif success and branch_name:
        header = f"Agent fixed `{package}` on `{branch}`, pushed branch `{branch_name}`"
        if pr_url:
            message = f"{header}\nPR: {pr_url}"
        else:
            message = (
                f"{header}\n"
                f"Create PR: https://git.almalinux.org/autopatch/{package}/compare/{target}...{branch_name}"
            )
    elif dry_run:
        message = f"Agent dry-run for `{package}` on `{branch}`: {summary}"
    else:
        message = f"Agent failed to fix `{package}` on `{branch}`: {summary}"
    client.chat_postMessage(
        channel=CHAT_NAME,
        text=message
    )
