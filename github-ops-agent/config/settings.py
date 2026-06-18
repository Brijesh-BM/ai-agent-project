"""
config/settings.py — Centralised config loaded from .env
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "owner/repo")  # e.g. "brijesh/placementhub"

    # Slack
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#ops-alerts")

    # Agent behaviour
    POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES", "30"))
    MAX_ISSUES_PER_RUN: int = int(os.getenv("MAX_ISSUES_PER_RUN", "20"))
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # Logging
    LOG_DIR: str = "logs"
    LOG_FILE: str = "logs/agent.log"

    def validate(self):
        missing = []
        if not self.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if not self.GITHUB_TOKEN:
            missing.append("GITHUB_TOKEN")
        if missing:
            raise EnvironmentError(
                f"Missing required env vars: {', '.join(missing)}\n"
                "Create a .env file — see .env.example"
            )


settings = Settings()
