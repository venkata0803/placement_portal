"""
email_helper.py - Reusable Email Helper (Stage 9.3 / 9.4)

Email flow (do not change scheduling — that lives in celery_app.py Beat):

1. Celery Beat triggers send_daily_reminders (daily) or generate_monthly_report (monthly).
2. tasks.py builds HTML via build_*_html helpers below.
3. send_email() delivers one message through Flask-Mail → MailHog (local SMTP).
4. Caller (tasks.py) logs success/failure and continues with remaining recipients.

Daily Reminder types (students):
  - Upcoming placement-drive deadline (within 2 days)
  - Upcoming interview schedule (within 24 hours)

Monthly Report (admin):
  - HTML placement statistics emailed to the admin account
"""

import logging

from flask_mail import Message

from extensions import mail

logger = logging.getLogger(__name__)


def build_drive_reminder_html(student_name, drive_title, company_name, deadline):
    """Simple HTML body for a placement-drive deadline reminder."""
    return f"""
    <html>
      <body>
        <p>Hello {student_name},</p>
        <p><strong>Reminder Type:</strong> Placement Drive Deadline</p>
        <p><strong>Drive Title:</strong> {drive_title}</p>
        <p><strong>Company:</strong> {company_name}</p>
        <p><strong>Deadline:</strong> {deadline}</p>
        <p>Please apply on the Placement Portal before the deadline.</p>
      </body>
    </html>
    """


def build_interview_reminder_html(
    student_name,
    drive_title,
    company_name,
    interview_date,
    interview_time,
    interview_mode,
):
    """Simple HTML body for an upcoming-interview reminder."""
    return f"""
    <html>
      <body>
        <p>Hello {student_name},</p>
        <p><strong>Reminder Type:</strong> Upcoming Interview</p>
        <p><strong>Drive Title:</strong> {drive_title}</p>
        <p><strong>Company:</strong> {company_name}</p>
        <p><strong>Interview Date:</strong> {interview_date}</p>
        <p><strong>Interview Time:</strong> {interview_time}</p>
        <p><strong>Interview Mode:</strong> {interview_mode}</p>
        <p>Please be prepared and join on time.</p>
      </body>
    </html>
    """


def send_email(to_email, subject, html_body):
    """
    Send one HTML email via Flask-Mail.

    Returns True on success, False on failure.
    Failures are logged; the Celery job continues for other recipients.
    """
    if not to_email:
        logger.warning("Email skipped: empty recipient (subject=%s)", subject)
        return False

    try:
        message = Message(
            subject=subject,
            recipients=[to_email],
            html=html_body,
        )
        mail.send(message)
        logger.info("Email sent to %s | subject=%s", to_email, subject)
        return True
    except Exception as error:
        # Keep going for other students if one email fails
        logger.error(
            "Email failed for %s | subject=%s | error=%s",
            to_email,
            subject,
            error,
        )
        print(f"Email failed for {to_email}: {error}")
        return False
