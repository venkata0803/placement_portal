"""
celery_worker.py - Celery Worker Entry Point (Stage 9.2 / 9.3 / 9.4)

Start the worker from the backend folder:

    celery -A celery_worker.celery worker --loglevel=info

On Windows, if the worker fails to start, use the solo pool:

    celery -A celery_worker.celery worker --loglevel=info --pool=solo

Start Celery Beat (scheduler) in a second terminal:

    celery -A celery_worker.celery beat --loglevel=info

Or run worker + beat together (handy on Windows):

    celery -A celery_worker.celery worker --beat --loglevel=info --pool=solo

Registered tasks include:
  - hello_task
  - send_daily_reminders    (Stage 9.3)
  - generate_monthly_report (Stage 9.4)
  - export_student_csv      (Stage 9.5)
  - export_company_csv      (Stage 9.5)
"""

import os
import sys

# Ensure the backend folder is on sys.path so "import app" works inside tasks
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from celery_app import celery

# Importing tasks registers @celery.task functions with this worker
import tasks  # noqa: F401
