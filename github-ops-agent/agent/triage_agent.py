"""
agent/triage_agent.py — The brain of the GitHub Ops Agent.

Uses Claude with tool use to:
1. Fetch open issues & PRs from GitHub
2. Classify each one (bug / feature / question / critical)
3. Draft a suggested response
4. Post a Slack alert for critical items
5. Log everything to SQLite
"""

import json
import anthropic
from config.settings import settings
from tools.github_tool import (
    fetch_open_issues,
    fetch_open_prs,
    add_label_to_issue,
    post_comment_on_issue,
)
from tools.slack_tool import send_slack_message
from tools.db_tool import log_event, mark_issue_processed, is_issue_processed


# ── Tool definitions (what Claude can call) ──────────────────────────────────

TOOLS = [
    {
        "name": "fetch_open_issues",
        "description": "Fetch a list of open issues from the GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of issues to fetch (default 10)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "fetch_open_prs",
        "description": "Fetch a list of open pull requests from the GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of PRs to fetch (default 10)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "add_label_to_issue",
        "description": "Add a label to a GitHub issue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "Issue number"},
                "label": {
                    "type": "string",
                    "description": "Label to add: 'bug', 'feature', 'question', 'critical', 'needs-review'",
                },
            },
            "required": ["issue_number", "label"],
        },
    },
    {
        "name": "post_comment_on_issue",
        "description": "Post a comment on a GitHub issue (e.g. a triage summary or suggested fix).",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "Issue number"},
                "comment": {"type": "string", "description": "Comment text to post"},
            },
            "required": ["issue_number", "comment"],
        },
    },
    {
        "name": "send_slack_alert",
        "description": "Send a Slack alert for critical or urgent items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Alert message to send"},
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Urgency level",
                },
            },
            "required": ["message", "urgency"],
        },
    },
    {
        "name": "log_event",
        "description": "Log a triage event to the database for reporting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer"},
                "title": {"type": "string"},
                "classification": {
                    "type": "string",
                    "enum": ["bug", "feature", "question", "critical", "pr-review"],
                },
                "action_taken": {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": [
                "issue_number",
                "title",
                "classification",
                "action_taken",
                "summary",
            ],
        },
    },
]

# ── Tool dispatcher ───────────────────────────────────────────────────────────

def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    """Execute the tool Claude requested and return the result as a string."""
    try:
        if tool_name == "fetch_open_issues":
            result = fetch_open_issues(limit=tool_input.get("limit", 10))
            return json.dumps(result)

        elif tool_name == "fetch_open_prs":
            result = fetch_open_prs(limit=tool_input.get("limit", 10))
            return json.dumps(result)

        elif tool_name == "add_label_to_issue":
            success = add_label_to_issue(
                issue_number=tool_input["issue_number"],
                label=tool_input["label"],
            )
            return json.dumps({"success": success})

        elif tool_name == "post_comment_on_issue":
            success = post_comment_on_issue(
                issue_number=tool_input["issue_number"],
                comment=tool_input["comment"],
            )
            return json.dumps({"success": success})

        elif tool_name == "send_slack_alert":
            success = send_slack_message(
                message=tool_input["message"],
                urgency=tool_input.get("urgency", "medium"),
            )
            return json.dumps({"success": success})

        elif tool_name == "log_event":
            log_event(
                issue_number=tool_input["issue_number"],
                title=tool_input["title"],
                classification=tool_input["classification"],
                action_taken=tool_input["action_taken"],
                summary=tool_input["summary"],
            )
            return json.dumps({"logged": True})

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Main Agent Class ─────────────────────────────────────────────────────────

class TriageAgent:
    def __init__(self):
        settings.validate()
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL

    def _system_prompt(self) -> str:
        return """You are a GitHub Ops Agent. Your job is to triage open issues and pull requests
for a software repository and take appropriate actions.

For each issue or PR you find, you must:
1. Classify it as one of: bug, feature, question, critical, pr-review
2. Add the appropriate label using the add_label_to_issue tool
3. If it's critical (security issue, data loss, production down), send a Slack alert immediately
4. Post a short helpful triage comment on the issue using post_comment_on_issue
5. Log the event using log_event

Classification rules:
- bug: Something is broken or not working as expected
- feature: A new feature request or enhancement
- question: User asking for help or clarification
- critical: Security vulnerability, data loss risk, or production incident
- pr-review: Pull request that needs review

Be concise in comments. Don't post generic comments — be specific to the issue content.
Work through all issues and PRs systematically. Use tools to take real actions.
"""

    def run(self):
        """Run the full triage loop."""
        print(f"\n{'='*50}")
        print("GitHub Ops Agent — Starting Triage Run")
        print(f"Repo: {settings.GITHUB_REPO}")
        print(f"{'='*50}\n")

        messages = [
            {
                "role": "user",
                "content": (
                    f"Please triage the open issues and pull requests for {settings.GITHUB_REPO}. "
                    f"Fetch up to {settings.MAX_ISSUES_PER_RUN} items, classify each one, "
                    "add labels, post comments, send Slack alerts for critical items, "
                    "and log everything. Start now."
                ),
            }
        ]

        # Agentic loop — Claude keeps running until it stops calling tools
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._system_prompt(),
                tools=TOOLS,
                messages=messages,
            )

            print(f"[Claude] Stop reason: {response.stop_reason}")

            # Extract and print any text Claude outputs
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"[Claude] {block.text}")

            # If Claude is done (no more tool calls), exit the loop
            if response.stop_reason == "end_turn":
                print("\n✅ Triage complete.")
                break

            # If Claude wants to use tools, execute them and feed results back
            if response.stop_reason == "tool_use":
                # Add Claude's response to message history
                messages.append({"role": "assistant", "content": response.content})

                # Execute each tool Claude requested
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"[Tool] Calling: {block.name}({json.dumps(block.input, indent=2)})")
                        result = dispatch_tool(block.name, block.input)
                        print(f"[Tool] Result: {result}\n")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                # Feed tool results back to Claude
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop reason — exit safely
                print(f"[Agent] Unexpected stop reason: {response.stop_reason}")
                break

        return True
