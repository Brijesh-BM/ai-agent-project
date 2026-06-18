"""
scheduler/cron.py — APScheduler-based cron runner.

Runs the triage agent every N minutes and sends a daily digest at 6pm.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from config.settings import settings
from agent.triage_agent import TriageAgent
from agent.reporter import Reporter


def run_triage():
    print("\n⏰ Scheduled triage starting...")
    agent = TriageAgent()
    agent.run()


def run_daily_report():
    print("\n📊 Sending daily digest...")
    reporter = Reporter()
    reporter.send_daily_digest()


def start_scheduler():
    scheduler = BlockingScheduler()

    # Triage every N minutes (default 30)
    scheduler.add_job(
        run_triage,
        trigger="interval",
        minutes=settings.POLL_INTERVAL_MINUTES,
        id="triage_job",
    )

    # Daily digest at 6pm every day
    scheduler.add_job(
        run_daily_report,
        trigger=CronTrigger(hour=18, minute=0),
        id="digest_job",
    )

    print(f"✅ Scheduler started:")
    print(f"   - Triage: every {settings.POLL_INTERVAL_MINUTES} minutes")
    print(f"   - Daily digest: 6:00 PM")
    print("   Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped.")
        scheduler.shutdown()
