# 🤖 GitHub Ops Agent

An autonomous AI agent that monitors GitHub repositories, triages issues and PRs using Claude, and takes real actions — labelling, commenting, alerting, and reporting — without any human intervention.

Built with Python + Anthropic Claude API (tool use) + GitHub REST API + Slack API.

---

## What it does

Every 30 minutes (configurable), the agent:

1. **Fetches** open issues and pull requests from your repo
2. **Reasons** about each one using Claude — classifies as `bug`, `feature`, `question`, `critical`, or `pr-review`
3. **Acts** — adds the correct label, posts a triage comment, sends a Slack alert for critical items
4. **Logs** everything to a local SQLite database
5. **Reports** — sends a daily digest to Slack at 6 PM summarising all activity

---

## Project Structure

```
github-ops-agent/
├── main.py                   # Entry point
├── requirements.txt
├── .env.example              # Copy to .env and fill in values
│
├── agent/
│   ├── triage_agent.py       # Core agent — Claude reasoning + tool use loop
│   └── reporter.py           # Daily digest generator
│
├── tools/
│   ├── github_tool.py        # GitHub REST API wrapper
│   ├── slack_tool.py         # Slack API wrapper
│   └── db_tool.py            # SQLite logger
│
├── scheduler/
│   └── cron.py               # APScheduler — runs agent on a cron schedule
│
├── config/
│   └── settings.py           # Centralised config from .env
│
├── logs/                     # Auto-created — stores events.db
└── tests/
    └── test_agent.py         # Pytest tests
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/github-ops-agent
cd github-ops-agent
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...        # Get from console.anthropic.com
GITHUB_TOKEN=ghp_...                # GitHub → Settings → Developer settings → PAT
GITHUB_REPO=your-username/your-repo # e.g. brijesh/placementhub
SLACK_BOT_TOKEN=xoxb-...            # Optional — Slack API → Your App → OAuth
SLACK_CHANNEL=#ops-alerts           # Optional
```

### 3. Run

```bash
# One-time triage run
python main.py --mode poll

# Run on a schedule (polls every 30 min, digest at 6pm)
python main.py --mode scheduler

# Send daily digest now
python main.py --mode report
```

### 4. Run tests

```bash
pytest tests/ -v
```

---

## How the agent loop works

```
User triggers run
      │
      ▼
Claude receives: "Triage issues for repo X"
      │
      ▼
Claude calls: fetch_open_issues()
      │
      ▼
Agent executes tool → returns issue list
      │
      ▼
Claude reads each issue, decides:
  - Classification
  - Label to add
  - Comment to post
  - Alert if critical
      │
      ▼
Claude calls: add_label(), post_comment(), send_slack_alert(), log_event()
      │
      ▼
Agent executes each tool, returns results
      │
      ▼
Claude confirms actions taken → stops (end_turn)
```

This is the **perception → reasoning → action** loop — the core pattern behind every production AI agent.

---

## Deployment (Railway)

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables in Railway dashboard
4. Set start command: `python main.py --mode scheduler`
5. Deploy — it runs 24/7 for free

---

## Resume bullet points

> Built an autonomous GitHub triage agent using Claude API (tool use) that classifies issues, auto-labels PRs, sends Slack alerts for critical items, and delivers daily digests — reducing manual repo maintenance to zero.

> Implemented an agentic loop (perception → reasoning → action) with 6 callable tools, SQLite event logging, and APScheduler for cron-based execution. Deployed on Railway.

---

## What to build next

- Add a FastAPI web dashboard to view triage history
- Support multiple repos
- Add email digest fallback when Slack is not configured
- Integrate with the IoT Anomaly Detection Agent for a unified ops system
