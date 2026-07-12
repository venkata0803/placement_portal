"""
email_helper.py - Reusable Email Helper (Stage 9.3)

One place to build reminder HTML and send mail.
Celery tasks call these helpers so email logic is not duplicated.
"""

from flask_mail import Message

from extensions import mail


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
    Send one HTML email.

    Returns True on success, False on failure.
    Caller decides whether to count the student as sent or skipped.
    """
    if not to_email:
        return False

    try:
        message = Message(
            subject=subject,
            recipients=[to_email],
            html=html_body,
        )
        mail.send(message)
        return True
    except Exception as error:
        # Keep going for other students if one email fails
        print(f"Email failed for {to_email}: {error}")
        return False
