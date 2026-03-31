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

def agent_result_message(
    package: str,
    branch: str,
    success: bool,
    summary: str,
    branch_name: str | None = None,
    dry_run: bool = False,
    config_branch: str | None = None,
    pr_url: str | None = None,
):
    target = config_branch or branch
    if success and branch_name:
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
