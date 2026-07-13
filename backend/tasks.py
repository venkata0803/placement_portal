"""
tasks.py - Celery Tasks (Stage 9.2 / 9.3 / 9.4 / 9.5)

Stage 9.2: hello_task (demo)
Stage 9.3: send_daily_reminders (email reminders via Celery Beat)
Stage 9.4: generate_monthly_report (HTML report emailed to admin)
Stage 9.5: export_student_csv / export_company_csv (async CSV files)

Email scheduling is configured in celery_app.py (Beat). Do not change schedules here.

Daily reminder flow:
  Beat → send_daily_reminders → _send_drive_reminders + _send_interview_reminders
  → email_helper.send_email → Flask-Mail → MailHog (local SMTP)

Monthly report flow:
  Beat → generate_monthly_report → report_service HTML → email admin
"""

import logging
from datetime import datetime, timedelta

from celery_app import celery

logger = logging.getLogger(__name__)


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


def _eligibility_skip_reason(student, drive):
    """Return a human-readable eligibility skip reason, or None if eligible."""
    eligible_branches = _normalize_branch_list(drive.eligible_branch)
    student_branch = (student.branch or "").strip().upper()

    if eligible_branches and student_branch not in eligible_branches:
        return (
            f"branch mismatch (student={student_branch or 'N/A'}, "
            f"need={eligible_branches})"
        )
    if student.cgpa < float(drive.minimum_cgpa):
        return f"CGPA too low ({student.cgpa} < {drive.minimum_cgpa})"
    if int(student.year) != int(drive.eligible_year):
        return (
            f"year mismatch (student={student.year}, "
            f"need={drive.eligible_year})"
        )
    return None


def _log_student_skip(
    student_id,
    email,
    drive_title,
    reason,
    *,
    interview_date=None,
    deadline=None,
    now=None,
):
    """Print + log a clear per-student skip explanation for debugging demos."""
    lines = [
        f"Student {student_id}",
        f"Email: {email or '(none)'}",
        f"Drive: {drive_title or '(none)'}",
    ]
    if interview_date is not None:
        lines.append(f"Interview: {interview_date}")
    if deadline is not None:
        lines.append(f"Deadline: {deadline}")
    if now is not None:
        lines.append(f"Today: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append(f"Reason: {reason}")
    message = "\n".join(lines)
    print(message)
    print("---")
    logger.info(
        "Reminder skipped | student_id=%s email=%s drive=%s reason=%s",
        student_id,
        email,
        drive_title,
        reason,
    )


def _reminder_windows(app_config):
    """Read reminder windows from Flask config (env-backed)."""
    reminder_days = int(app_config.get("REMINDER_DAYS", 2))
    interview_days = int(app_config.get("INTERVIEW_REMINDER_DAYS", 1))
    return max(reminder_days, 0), max(interview_days, 0)


def _send_drive_reminders(now, stats, *, bypass_date_window=False, reminder_days=2):
    """
    Email eligible students about Approved drives whose deadline is within
    REMINDER_DAYS (default 2).

    When bypass_date_window=True (manual /admin/test-reminder under DEBUG only):
    include all Approved drives with a future deadline (ignore upper window).
    """
    from models import Application, PlacementDrive, Student
    from email_helper import build_drive_reminder_html, send_email

    window_end = now + timedelta(days=reminder_days)
    query = PlacementDrive.query.filter(
        PlacementDrive.status == "Approved",
        PlacementDrive.application_deadline >= now,
    )
    if not bypass_date_window:
        query = query.filter(PlacementDrive.application_deadline <= window_end)

    drives = query.all()
    stats["drives_checked"] = len(drives)
    mode = "BYPASS window" if bypass_date_window else f"within {reminder_days} day(s)"
    logger.info(
        "Deadline reminders: checking %s approved drives (%s)",
        len(drives),
        mode,
    )
    print(
        f"Drive reminder mode: {mode} | now={now.isoformat()} "
        f"| window_end={window_end.isoformat()} | drives={len(drives)}"
    )

    # Active students only — blacklisted students cannot apply
    students = Student.query.filter_by(is_blacklisted=False).all()
    blacklisted_count = Student.query.filter_by(is_blacklisted=True).count()
    if blacklisted_count:
        print(f"Blacklisted students excluded from drive loop: {blacklisted_count}")

    for drive in drives:
        company = drive.company
        if company is not None and getattr(company, "is_blacklisted", False):
            print(
                f"Drive {drive.id} ({drive.job_title}): skipped — company blacklisted"
            )
            stats["students_skipped"] += len(students)
            continue

        company_name = company.company_name if company else ""
        deadline_text = (
            drive.application_deadline.strftime("%Y-%m-%d %H:%M")
            if drive.application_deadline
            else ""
        )

        for student in students:
            email = student.user.email if student.user else None
            eligibility_reason = _eligibility_skip_reason(student, drive)
            if eligibility_reason:
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id,
                    email,
                    drive.job_title,
                    eligibility_reason,
                    deadline=deadline_text,
                    now=now,
                )
                continue

            if _already_applied(student.id, drive.id, Application):
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id,
                    email,
                    drive.job_title,
                    "already applied",
                    deadline=deadline_text,
                    now=now,
                )
                continue

            if not email:
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id,
                    email,
                    drive.job_title,
                    "no email",
                    deadline=deadline_text,
                    now=now,
                )
                continue

            try:
                html = build_drive_reminder_html(
                    student_name=student.full_name,
                    drive_title=drive.job_title,
                    company_name=company_name,
                    deadline=deadline_text,
                )
                print(
                    f"Calling send_email for student {student.id} "
                    f"({email}) | drive deadline reminder | {drive.job_title}"
                )
                sent = send_email(email, "Placement Portal Reminder", html)
                if sent:
                    stats["emails_sent"] += 1
                    logger.info(
                        "Deadline reminder sent to %s for drive '%s'",
                        email,
                        drive.job_title,
                    )
                else:
                    stats["students_skipped"] += 1
                    _log_student_skip(
                        student.id,
                        email,
                        drive.job_title,
                        "send_email returned False",
                        deadline=deadline_text,
                        now=now,
                    )
            except Exception as error:
                stats["errors"] += 1
                stats["students_skipped"] += 1
                logger.error(
                    "Deadline reminder failed for student_id=%s drive_id=%s: %s",
                    student.id,
                    drive.id,
                    error,
                )
                _log_student_skip(
                    student.id,
                    email,
                    drive.job_title,
                    f"exception: {error}",
                    deadline=deadline_text,
                    now=now,
                )


def _send_interview_reminders(
    now,
    stats,
    *,
    bypass_date_window=False,
    interview_reminder_days=1,
):
    """
    Email students whose interview is within INTERVIEW_REMINDER_DAYS (default 1).

    When bypass_date_window=True (manual /admin/test-reminder under DEBUG only):
    include all upcoming interviews (interview_dt >= now), ignore upper window.
    """
    from models import Application
    from email_helper import build_interview_reminder_html, send_email

    window_end = now + timedelta(days=interview_reminder_days)

    applications = Application.query.filter(
        Application.status == "Interview",
        Application.interview_date.isnot(None),
    ).all()
    stats["interviews_checked"] = len(applications)
    mode = (
        "BYPASS window"
        if bypass_date_window
        else f"within {interview_reminder_days} day(s)"
    )
    logger.info(
        "Interview reminders: checking %s interview applications (%s)",
        len(applications),
        mode,
    )
    print(
        f"Interview reminder mode: {mode} | now={now.isoformat()} "
        f"| window_end={window_end.isoformat()} | interviews={len(applications)}"
    )

    for application in applications:
        student = application.student
        drive = application.drive
        email = (
            student.user.email
            if student and student.user
            else None
        )
        drive_title = drive.job_title if drive else None
        interview_text = (
            f"{application.interview_date} {application.interview_time or ''}".strip()
        )

        try:
            interview_dt = _parse_interview_datetime(
                application.interview_date,
                application.interview_time,
            )
            if interview_dt is None:
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id if student else application.student_id,
                    email,
                    drive_title,
                    "interview date/time could not be parsed",
                    interview_date=interview_text,
                    now=now,
                )
                continue

            if interview_dt < now:
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id if student else application.student_id,
                    email,
                    drive_title,
                    "interview already past",
                    interview_date=interview_text,
                    now=now,
                )
                continue

            if not bypass_date_window and interview_dt > window_end:
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id if student else application.student_id,
                    email,
                    drive_title,
                    (
                        "Interview not within reminder window "
                        f"(need <= {window_end.strftime('%Y-%m-%d %H:%M')} UTC)"
                    ),
                    interview_date=interview_text,
                    now=now,
                )
                continue

            if not student or not drive:
                stats["students_skipped"] += 1
                _log_student_skip(
                    application.student_id,
                    email,
                    drive_title,
                    "missing student or drive record",
                    interview_date=interview_text,
                    now=now,
                )
                continue
            if student.is_blacklisted:
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id,
                    email,
                    drive_title,
                    "blacklisted",
                    interview_date=interview_text,
                    now=now,
                )
                continue
            if not email:
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id,
                    email,
                    drive_title,
                    "no email",
                    interview_date=interview_text,
                    now=now,
                )
                continue

            company_name = drive.company.company_name if drive.company else ""
            html = build_interview_reminder_html(
                student_name=student.full_name,
                drive_title=drive.job_title,
                company_name=company_name,
                interview_date=str(application.interview_date),
                interview_time=application.interview_time or "",
                interview_mode=application.interview_mode or "",
            )
            print(
                f"Calling send_email for student {student.id} "
                f"({email}) | interview reminder | {drive.job_title}"
            )
            sent = send_email(email, "Placement Portal Reminder", html)
            if sent:
                stats["emails_sent"] += 1
                logger.info(
                    "Interview reminder sent to %s for drive '%s'",
                    email,
                    drive.job_title,
                )
            else:
                stats["students_skipped"] += 1
                _log_student_skip(
                    student.id,
                    email,
                    drive_title,
                    "send_email returned False",
                    interview_date=interview_text,
                    now=now,
                )
        except Exception as error:
            stats["errors"] += 1
            stats["students_skipped"] += 1
            logger.error(
                "Interview reminder failed for application_id=%s: %s",
                application.id,
                error,
            )
            _log_student_skip(
                application.student_id,
                email,
                drive_title,
                f"exception: {error}",
                interview_date=interview_text,
                now=now,
            )


@celery.task(name="send_daily_reminders")
def send_daily_reminders(bypass_date_window=False):
    """
    Stage 9.3 mandatory daily reminder job.

    Runs on Celery Beat (9:00 AM, or every minute in test mode).
    Can also be triggered immediately by POST /admin/test-reminder.

    bypass_date_window:
      False (default / Beat) → enforce REMINDER_DAYS / INTERVIEW_REMINDER_DAYS
      True  → only from /admin/test-reminder when Flask DEBUG=True;
              still requires upcoming deadlines/interviews + eligibility,
              but ignores the upper reminder window for demo purposes.

    Sends:
      1) Upcoming deadline reminders to eligible students
      2) Interview schedule reminders
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
        "errors": 0,
        "bypass_date_window": bool(bypass_date_window),
    }

    with app.app_context():
        now = datetime.utcnow()
        reminder_days, interview_days = _reminder_windows(app.config)
        stats["reminder_days"] = reminder_days
        stats["interview_reminder_days"] = interview_days

        print("=== Daily Reminder Job Started ===")
        print(f"Current UTC time: {now.isoformat()}")
        print(f"bypass_date_window: {bypass_date_window}")
        print(f"REMINDER_DAYS: {reminder_days}")
        print(f"INTERVIEW_REMINDER_DAYS: {interview_days}")
        logger.info(
            "Daily reminder job started at %s UTC | bypass=%s | "
            "reminder_days=%s interview_days=%s",
            now.isoformat(),
            bypass_date_window,
            reminder_days,
            interview_days,
        )

        try:
            _send_drive_reminders(
                now,
                stats,
                bypass_date_window=bypass_date_window,
                reminder_days=reminder_days,
            )
            _send_interview_reminders(
                now,
                stats,
                bypass_date_window=bypass_date_window,
                interview_reminder_days=interview_days,
            )
        except Exception as error:
            stats["errors"] += 1
            logger.exception("Daily reminder job failed: %s", error)
            print(f"Daily reminder job error: {error}")

        # Required logging for Stage 9.3
        print(f"Emails sent: {stats['emails_sent']}")
        print(f"Students skipped: {stats['students_skipped']}")
        print(f"Drives checked: {stats['drives_checked']}")
        print(f"Interviews checked: {stats['interviews_checked']}")
        print(f"Errors: {stats['errors']}")
        print("=== Daily Reminder Job Finished ===")
        logger.info(
            "Daily reminder finished | emails_sent=%s skipped=%s drives=%s "
            "interviews=%s errors=%s bypass=%s",
            stats["emails_sent"],
            stats["students_skipped"],
            stats["drives_checked"],
            stats["interviews_checked"],
            stats["errors"],
            bypass_date_window,
        )

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

    Scheduled: 1st of every month at 09:00 AM (Asia/Kolkata) — see celery_app.py.
    Manual test: POST /admin/test-monthly-report

    Flow: collect DB stats → build HTML → email admin via Flask-Mail.
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
        logger.info("Monthly report job started")

        try:
            # Step 1: collect CURRENT MONTH counts from the database
            stats = collect_report_statistics()
            result["statistics"] = stats
            print("Report Generated")
            print(f"Statistics: {stats}")
            logger.info("Monthly report statistics collected: %s", stats)

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
                logger.info("Monthly HTML report emailed to admin %s", admin_email)
            else:
                print("Email Sent: False (check admin email / MAIL settings)")
                logger.warning(
                    "Monthly report email failed for admin %s",
                    admin_email,
                )
        except Exception as error:
            result["error"] = str(error)
            logger.exception("Monthly report job failed: %s", error)
            print(f"Monthly report job error: {error}")

        print("Task Finished")
        print("=== Monthly Report Job Finished ===")
        logger.info(
            "Monthly report finished | report_generated=%s email_sent=%s",
            result["report_generated"],
            result["email_sent"],
        )

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
