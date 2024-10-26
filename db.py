import os
import sqlite3
from datetime import datetime, timedelta, timezone

from telegram.ext import (
    Application,
)
from telegram.ext._utils.types import JobCallback

DB_PATH = os.path.join(os.getenv("VOLUME_MOUNT_PATH", "."), "jobs.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            interval TEXT,
            next_run_time TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


def save_job_to_db(
    job_id: str,
    chat_id: int,
    user_id: int,
    message: str,
    interval: str,
    next_run_time: str,
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO jobs (id,chat_id, user_id, message, interval, next_run_time)
        VALUES (?,?, ?, ?, ?, ?)
    """,
        (job_id, chat_id, user_id, message, interval, next_run_time),
    )
    job_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return job_id


def remove_job_from_db(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def update_job_next_run_time(job_id: str, next_run_time: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE jobs SET next_run_time = ? WHERE id = ?",
        (next_run_time, job_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_jobs_from_db(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, chat_id, user_id, message, interval, next_run_time FROM jobs WHERE chat_id = ?",
        (chat_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return (dict(row) for row in rows) if rows else None


def get_job_from_db(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, chat_id, user_id, message, interval, next_run_time FROM jobs WHERE id = ?",
        (job_id,),
    )
    job = cursor.fetchone()
    conn.close()
    return dict(job) if job else None


def load_jobs_from_db(application: Application, reminder_callback: JobCallback):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id,chat_id, user_id, message, interval, next_run_time FROM jobs"
    )
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        job_id, chat_id, user_id, message, interval, next_run_time = row
        next_run_time = datetime.fromisoformat(next_run_time)
        now = datetime.now(timezone.utc)
        if next_run_time < now:
            if interval:
                # Calculate the next valid run time for repeating jobs
                intervals = {
                    "daily": timedelta(days=1),
                    "weekly": timedelta(weeks=1),
                    "hourly": timedelta(hours=1),
                }
                missed_time = now - next_run_time
                interval_delta = intervals[interval]
                missed_intervals = (missed_time // interval_delta) + 1
                next_run_time += missed_intervals * interval_delta
                update_job_next_run_time(job_id, next_run_time.isoformat())
            else:
                # Remove non-repeating jobs with past run times
                remove_job_from_db(job_id)
                continue
        if interval:
            intervals = {
                "daily": timedelta(days=1),
                "weekly": timedelta(weeks=1),
                "hourly": timedelta(hours=1),
            }
            application.job_queue.run_repeating(
                reminder_callback,
                interval=intervals[interval],
                first=(next_run_time - datetime.now(timezone.utc)).total_seconds(),
                chat_id=chat_id,
                user_id=user_id,
                name=str(chat_id),
                data=message,
            )
        else:
            application.job_queue.run_once(
                reminder_callback,
                next_run_time,
                chat_id=chat_id,
                user_id=user_id,
                name=str(chat_id),
                data=message,
            )
