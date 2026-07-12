"""
celery_app.py - Celery Application (Stage 9.2 / 9.3)

Creates the Celery instance used by:
  - the worker process (celery_worker.py)
  - Celery Beat (scheduled daily reminders)
  - Flask routes that call .delay() (e.g. /test-celery, /admin/test-reminder)

Broker  = Redis  (where Flask / Beat send new jobs)
Backend = Redis  (where task results are stored)

We only import Config here — not Flask app — to avoid circular imports.
"""

from celery import Celery
from celery.schedules import crontab

from config import Config


def _build_beat_schedule():
    """
    Celery Beat schedules (Stage 9.3 + 9.4).

    Daily reminders (9.3):
      Production -> every day at 9:00 AM (Asia/Kolkata)
      Testing    -> every 1 minute when CELERY_BEAT_TEST_MODE=true

    Monthly report (9.4):
      Production -> 1st day of every month at 9:00 AM
      Testing    -> use POST /admin/test-monthly-report (manual trigger)
    """
    if Config.CELERY_BEAT_TEST_MODE:
        # Easy local testing — reminder runs about once per minute
        reminder_schedule = 60.0
        print("Celery Beat: TEST MODE — daily reminders every 1 minute")
    else:
        # Production — 9:00 AM local timezone (see timezone below)
        reminder_schedule = crontab(hour=9, minute=0)
        print("Celery Beat: PRODUCTION — daily reminders at 09:00 Asia/Kolkata")

    # Always schedule monthly report for the 1st at 09:00
    monthly_schedule = crontab(day_of_month=1, hour=9, minute=0)
    print("Celery Beat: monthly report on day 1 at 09:00 Asia/Kolkata")

    return {
        "daily-reminder": {
            "task": "send_daily_reminders",
            "schedule": reminder_schedule,
        },
        "monthly-report": {
            "task": "generate_monthly_report",
            "schedule": monthly_schedule,
        },
    }


def make_celery():
    """
    Build a Celery app that talks to Redis.

    broker  -> queue that holds waiting tasks
    backend -> storage for task status / return values
    include -> modules that define @celery.task functions
    """
    celery_instance = Celery(
        "placement_portal",
        broker=Config.REDIS_URL,
        backend=Config.REDIS_URL,
        include=["tasks"],
    )

    # Keep settings simple and beginner-friendly
    celery_instance.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        timezone="Asia/Kolkata",
        enable_utc=True,
        beat_schedule=_build_beat_schedule(),
    )

    return celery_instance


# Shared Celery object imported by tasks.py and celery_worker.py
celery = make_celery()
