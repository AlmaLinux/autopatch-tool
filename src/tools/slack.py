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
