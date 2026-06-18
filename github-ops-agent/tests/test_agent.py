"""
tests/test_agent.py — Basic tests for the GitHub Ops Agent.

Run with: pytest tests/
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from agent.triage_agent import dispatch_tool


class TestDispatchTool:
    """Test the tool dispatcher with mocked GitHub/Slack calls."""

    @patch("agent.triage_agent.fetch_open_issues")
    def test_fetch_issues_tool(self, mock_fetch):
        mock_fetch.return_value = [
            {"number": 1, "title": "Login button broken", "body": "Clicking login does nothing"}
        ]
        result = dispatch_tool("fetch_open_issues", {"limit": 5})
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["number"] == 1
        mock_fetch.assert_called_once_with(limit=5)

    @patch("agent.triage_agent.send_slack_message")
    def test_slack_alert_tool(self, mock_slack):
        mock_slack.return_value = True
        result = dispatch_tool(
            "send_slack_alert",
            {"message": "Critical bug found!", "urgency": "critical"},
        )
        data = json.loads(result)
        assert data["success"] is True

    @patch("agent.triage_agent.log_event")
    def test_log_event_tool(self, mock_log):
        result = dispatch_tool(
            "log_event",
            {
                "issue_number": 42,
                "title": "Test issue",
                "classification": "bug",
                "action_taken": "labeled and commented",
                "summary": "A test bug was triaged",
            },
        )
        data = json.loads(result)
        assert data["logged"] is True

    def test_unknown_tool_returns_error(self):
        result = dispatch_tool("nonexistent_tool", {})
        data = json.loads(result)
        assert "error" in data


class TestSettings:
    def test_settings_missing_keys_raises(self):
        from config.settings import Settings
        s = Settings()
        s.ANTHROPIC_API_KEY = ""
        s.GITHUB_TOKEN = ""
        with pytest.raises(EnvironmentError) as exc:
            s.validate()
        assert "ANTHROPIC_API_KEY" in str(exc.value)
        assert "GITHUB_TOKEN" in str(exc.value)
