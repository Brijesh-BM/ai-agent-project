"""
GitHub Ops Agent — Main Entry Point
Run this to start the agent.

Usage:
  python main.py --mode poll       # One-time poll and triage
  python main.py --mode scheduler  # Runs on cron schedule
  python main.py --mode report     # Send daily digest now
"""

import argparse
from agent.triage_agent import TriageAgent
from scheduler.cron import start_scheduler
from agent.reporter import Reporter


def main():
    parser = argparse.ArgumentParser(description="GitHub Ops Agent")
    parser.add_argument(
        "--mode",
        choices=["poll", "scheduler", "report"],
        default="poll",
        help="Run mode: poll (one-time), scheduler (cron), report (daily digest)",
    )
    args = parser.parse_args()

    if args.mode == "poll":
        print("🤖 Running one-time GitHub triage...")
        agent = TriageAgent()
        agent.run()

    elif args.mode == "scheduler":
        print("⏰ Starting scheduled agent (polls every 30 min)...")
        start_scheduler()

    elif args.mode == "report":
        print("📊 Sending daily digest...")
        reporter = Reporter()
        reporter.send_daily_digest()


if __name__ == "__main__":
    main()
