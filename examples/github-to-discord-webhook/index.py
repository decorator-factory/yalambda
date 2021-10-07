import os
from typing import Any, Dict, Optional

import httpx
from yalambda import function, YaResponse

from github_issues import IssueEvent


# Load the webhook URL from an environment variable
# It should look like https://discord.com/api/webhooks/XXXXX/YYYYY

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]


# Create a Discord embed if one should be sent

def create_embed(event: IssueEvent) -> Optional[Dict[str, Any]]:
    issue = event.issue

    # If the event has an author, include it in the embed
    if issue.user is None:
        author = {}
    else:
        author = {
            "author": {
                "name": issue.user.login,
                "url": issue.user.html_url,
            },
            "thumbnail": {
                "url": issue.user.avatar_url,
            }
        }

    if event.action == "opened":
        return {
            "title": "New issue #{}".format(issue.number),
            "description": issue.title,
            "color": 0x42db72,
            "url": issue.html_url,
            **author,
        }
    elif event.action == "closed":
        return {
            "title": "Issue #{} closed".format(issue.number),
            "description": issue.title,
            "color": 0xed472d,
            "url": issue.html_url,
            **author,
        }
    else:
        return None


# Global state

client: httpx.AsyncClient

async def init():
    global client
    client = httpx.AsyncClient()


# Entry point

@function(init)
async def handler(event: IssueEvent) -> YaResponse:
    embed = create_embed(event)

    if embed is not None:
        await client.post(DISCORD_WEBHOOK, json={
            "embeds": [embed]
        })

    return YaResponse(200, "")
