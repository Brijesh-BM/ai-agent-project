"""
tools/slack_tool.py — Slack API wrapper.

Sends alerts and digest messages to a Slack channel.
"""

import requests
from config.settings import settings


URGENCY_EMOJI = {
    "low": "ℹ️",
    "medium": "⚠️",
    "high": "🔴",
    "critical": "🚨",
}


def send_slack_message(message: str, urgency: str = "medium") -> bool:
    """Send a message to the configured Slack channel."""
    if not settings.SLACK_BOT_TOKEN:
        print("  [Slack] No token configured — skipping Slack notification")
        return False

    emoji = URGENCY_EMOJI.get(urgency, "⚠️")
    formatted = f"{emoji} *GitHub Ops Agent*\n{message}"

    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "channel": settings.SLACK_CHANNEL,
        "text": formatted,
        "unfurl_links": False,
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    if data.get("ok"):
        print(f"  ✓ Slack message sent to {settings.SLACK_CHANNEL}")
        return True
    else:
        print(f"  ✗ Slack error: {data.get('error', 'Unknown error')}")
        return False


def send_digest(digest_text: str) -> bool:
    """Send the daily digest as a Slack message."""
    return send_slack_message(
        message=f"*📊 Daily GitHub Digest*\n\n{digest_text}",
        urgency="low",
    )
