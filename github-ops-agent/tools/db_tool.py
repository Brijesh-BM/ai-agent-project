"""
tools/db_tool.py — SQLite logger for triage events.

Stores every triage action so we can generate daily reports
and avoid re-processing the same issues.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "logs/events.db"


def _get_connection() -> sqlite3.Connection:
    os.makedirs("logs", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS triage_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_number    INTEGER NOT NULL,
            title           TEXT,
            classification  TEXT,
            action_taken    TEXT,
            summary         TEXT,
            processed_at    TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def log_event(
    issue_number: int,
    title: str,
    classification: str,
    action_taken: str,
    summary: str,
):
    """Log a single triage event."""
    init_db()
    conn = _get_connection()
    conn.execute(
        """
        INSERT INTO triage_events
            (issue_number, title, classification, action_taken, summary)
        VALUES (?, ?, ?, ?, ?)
        """,
        (issue_number, title, classification, action_taken, summary),
    )
    conn.commit()
    conn.close()
    print(f"  ✓ Event logged: #{issue_number} ({classification})")


def is_issue_processed(issue_number: int) -> bool:
    """Check if an issue was already processed today."""
    init_db()
    conn = _get_connection()
    row = conn.execute(
        """
        SELECT id FROM triage_events
        WHERE issue_number = ?
          AND date(processed_at) = date('now')
        LIMIT 1
        """,
        (issue_number,),
    ).fetchone()
    conn.close()
    return row is not None


def mark_issue_processed(issue_number: int):
    """Mark an issue as processed (alias for log_event with minimal data)."""
    log_event(
        issue_number=issue_number,
        title="",
        classification="processed",
        action_taken="marked",
        summary="",
    )


def get_today_events() -> list[dict]:
    """Get all events logged today for the daily digest."""
    init_db()
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT * FROM triage_events
        WHERE date(processed_at) = date('now')
        ORDER BY processed_at DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
