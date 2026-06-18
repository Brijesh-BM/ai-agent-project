"""
agent/reporter.py — Daily digest generator.

Pulls today's triage events from the DB, uses Claude to summarise them
into a readable digest, and sends it to Slack.
"""

import anthropic
from config.settings import settings
from tools.db_tool import get_today_events
from tools.slack_tool import send_digest


class Reporter:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def send_daily_digest(self):
        events = get_today_events()

        if not events:
            send_digest("No issues or PRs were processed today. ✅ All clear!")
            return

        # Build a summary string of today's events
        event_lines = []
        for e in events:
            event_lines.append(
                f"- #{e['issue_number']} [{e['classification']}]: {e['title']} → {e['action_taken']}"
            )
        events_text = "\n".join(event_lines)

        # Ask Claude to summarise it into a nice digest
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Here are today's GitHub triage events. "
                        "Write a short, clear daily digest (under 200 words) "
                        "suitable for a Slack message. Highlight any critical items first, "
                        "then summarise by category. Be concise.\n\n"
                        f"Events:\n{events_text}"
                    ),
                }
            ],
        )

        digest = response.content[0].text
        send_digest(digest)
        print(f"✅ Daily digest sent ({len(events)} events)")
