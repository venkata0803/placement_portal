"""
tasks.py - Celery Tasks (Stage 9.2 / 9.3 / 9.4 / 9.5)

Stage 9.2: hello_task (demo)
Stage 9.3: send_daily_reminders (email reminders via Celery Beat)
Stage 9.4: generate_monthly_report (HTML report emailed to admin)
Stage 9.5: export_student_csv / export_company_csv (async CSV files)
"""

from datetime import datetime, timedelta

from celery_app import celery


@celery.task(name="hello_task")
def hello_task():
    """
    Demo task to verify Celery + Redis are wired correctly.

    Returns a simple success string stored in the Redis result backend.
    """
    return "Celery Working Successfully"


# ---------- Stage 9.3: Daily Reminder helpers (keep each function short) ----------


def _parse_interview_datetime(interview_date, interview_time):
    """Combine interview_date + interview_time into one datetime."""
    if not interview_date:
        return None

    time_text = (interview_time or "00:00").strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            parsed_time = datetime.strptime(time_text, fmt).time()
            return datetime.combine(interview_date, parsed_time)
        except ValueError:
            continue

    # If time cannot be parsed, use midnight on that date
    return datetime.combine(interview_date, datetime.min.time())


def _normalize_branch_list(branch_text):
    """Turn 'CSE, ECE' into ['CSE', 'ECE']."""
    if not branch_text:
        return []
    parts = [p.strip().upper() for p in str(branch_text).split(",")]
    return [p for p in parts if p]


def _student_is_eligible(student, drive):
    """True when student matches drive branch, CGPA, and year."""
    eligible_branches = _normalize_branch_list(drive.eligible_branch)
    student_branch = (student.branch or "").strip().upper()

    if eligible_branches and student_branch not in eligible_branches:
        return False
    if student.cgpa < float(drive.minimum_cgpa):
        return False
    if int(student.year) != int(drive.eligible_year):
        return False
    return True


def _already_applied(student_id, drive_id, Application):
    """True if this student already has an application for the drive."""
    existing = Application.query.filter_by(
        student_id=student_id,
        drive_id=drive_id,
    ).first()
    return existing is not None


def _send_drive_reminders(now, stats):
    """
    Email eligible students about Approved drives
    whose deadline is within the next 2 days.
    """
    from models import Application, PlacementDrive, Student
    from email_helper import build_drive_reminder_html, send_email

    window_end = now + timedelta(days=2)

    drives = (
        PlacementDrive.query.filter(
            PlacementDrive.status == "Approved",
            PlacementDrive.application_deadline >= now,
            PlacementDrive.application_deadline <= window_end,
        ).all()
    )
    stats["drives_checked"] = len(drives)

    students = Student.query.all()

    for drive in drives:
        company_name = drive.company.company_name if drive.company else ""
        deadline_text = (
            drive.application_deadline.strftime("%Y-%m-%d %H:%M")
            if drive.application_deadline
            else ""
        )

        for student in students:
            # Skip students who cannot apply or already applied
            if not _student_is_eligible(student, drive):
                stats["students_skipped"] += 1
                continue
            if _already_applied(student.id, drive.id, Application):
                stats["students_skipped"] += 1
                continue

            email = student.user.email if student.user else None
            html = build_drive_reminder_html(
                student_name=student.full_name,
                drive_title=drive.job_title,
                company_name=company_name,
                deadline=deadline_text,
            )
            sent = send_email(email, "Placement Portal Reminder", html)
            if sent:
                stats["emails_sent"] += 1
            else:
                stats["students_skipped"] += 1


def _send_interview_reminders(now, stats):
    """
    Email students whose interview is scheduled
    within the next 24 hours.
    """
    from models import Application
    from email_helper import build_interview_reminder_html, send_email

    window_end = now + timedelta(hours=24)

    applications = Application.query.filter(
        Application.status == "Interview",
        Application.interview_date.isnot(None),
    ).all()
    stats["interviews_checked"] = len(applications)

    for application in applications:
        interview_dt = _parse_interview_datetime(
            application.interview_date,
            application.interview_time,
        )
        if interview_dt is None or not (now <= interview_dt <= window_end):
            stats["students_skipped"] += 1
            continue

        student = application.student
        drive = application.drive
        if not student or not drive:
            stats["students_skipped"] += 1
            continue

        company_name = drive.company.company_name if drive.company else ""
        email = student.user.email if student.user else None
        html = build_interview_reminder_html(
            student_name=student.full_name,
            drive_title=drive.job_title,
            company_name=company_name,
            interview_date=str(application.interview_date),
            interview_time=application.interview_time or "",
            interview_mode=application.interview_mode or "",
        )
        sent = send_email(email, "Placement Portal Reminder", html)
        if sent:
            stats["emails_sent"] += 1
        else:
            stats["students_skipped"] += 1


@celery.task(name="send_daily_reminders")
def send_daily_reminders():
    """
    Stage 9.3 mandatory daily reminder job.

    Runs on Celery Beat (9:00 AM, or every minute in test mode).
    Can also be triggered immediately by POST /admin/test-reminder.
    """
    _ensure_backend_on_path()

    # Import create_app inside the task to avoid circular imports at module load
    from app import create_app

    app = create_app()
    stats = {
        "emails_sent": 0,
        "students_skipped": 0,
        "drives_checked": 0,
        "interviews_checked": 0,
    }

    with app.app_context():
        now = datetime.utcnow()
        print("=== Daily Reminder Job Started ===")
        print(f"Current UTC time: {now.isoformat()}")

        _send_drive_reminders(now, stats)
        _send_interview_reminders(now, stats)

        # Required logging for Stage 9.3
        print(f"Emails sent: {stats['emails_sent']}")
        print(f"Students skipped: {stats['students_skipped']}")
        print(f"Drives checked: {stats['drives_checked']}")
        print(f"Interviews checked: {stats['interviews_checked']}")
        print("=== Daily Reminder Job Finished ===")

    return stats


def _ensure_backend_on_path():
    """
    Make sure the backend folder is importable inside the Celery worker.

    Without this, "from app import create_app" can fail in the worker process.
    """
    import os
    import sys

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)


@celery.task(name="generate_monthly_report")
def generate_monthly_report():
    """
    Stage 9.4: build the monthly placement HTML report and email the admin.

    Scheduled: 1st of every month at 09:00 AM (Asia/Kolkata).
    Manual test: POST /admin/test-monthly-report
    """
    _ensure_backend_on_path()

    # Import inside the task to avoid circular imports at module load time
    from app import create_app
    from email_helper import send_email
    from services.report_service import (
        build_monthly_report_html,
        collect_report_statistics,
        get_admin_email,
    )

    app = create_app()
    result = {
        "report_generated": False,
        "email_sent": False,
        "admin_email": None,
        "statistics": {},
    }

    with app.app_context():
        print("=== Monthly Report Job Started ===")

        # Step 1: collect counts from the database
        stats = collect_report_statistics()
        result["statistics"] = stats
        print("Report Generated")
        print(f"Statistics: {stats}")

        # Step 2: turn counts into Bootstrap HTML
        html_report = build_monthly_report_html(stats)

        # Step 3: email only the admin user
        admin_email = get_admin_email()
        result["admin_email"] = admin_email
        email_sent = send_email(
            admin_email,
            "Monthly Placement Report",
            html_report,
        )
        result["email_sent"] = email_sent
        result["report_generated"] = True

        if email_sent:
            print("Email Sent")
        else:
            print("Email Sent: False (check admin email / MAIL settings)")

        print("Task Finished")
        print("=== Monthly Report Job Finished ===")

    return result


@celery.task(name="export_student_csv")
def export_student_csv(student_id, filename):
    """
    Stage 9.5: write one student's application history to a CSV file.

    Queued by POST /student/export. File lands in backend/exports/.
    """
    _ensure_backend_on_path()

    from app import create_app
    from services.export_service import write_student_applications_csv

    app = create_app()
    result = {
        "filename": filename,
        "file_path": None,
        "rows": 0,
    }

    with app.app_context():
        print("CSV Started")
        file_path, row_count = write_student_applications_csv(student_id, filename)
        result["file_path"] = file_path
        result["rows"] = row_count
        print("CSV Generated")
        print(f"Rows: {row_count}")
        print(f"File Path: {file_path}")
        print("Finished")

    return result


@celery.task(name="export_company_csv")
def export_company_csv(drive_id, filename):
    """
    Stage 9.5: write applicants for one placement drive to a CSV file.

    Queued by POST /company/export/<drive_id>. File lands in backend/exports/.
    """
    _ensure_backend_on_path()

    from app import create_app
    from services.export_service import write_company_drive_csv

    app = create_app()
    result = {
        "filename": filename,
        "file_path": None,
        "rows": 0,
    }

    with app.app_context():
        print("CSV Started")
        file_path, row_count = write_company_drive_csv(drive_id, filename)
        result["file_path"] = file_path
        result["rows"] = row_count
        print("CSV Generated")
        print(f"Rows: {row_count}")
        print(f"File Path: {file_path}")
        print("Finished")

    return result
