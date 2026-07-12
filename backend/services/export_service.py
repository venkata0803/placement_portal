"""
export_service.py - CSV Export Helpers (Stage 9.5)

Builds student and company CSV files under backend/exports/.
Celery tasks call these functions so CSV writing stays in one place.
"""

import csv
import os
from datetime import datetime

from models import Application


def get_export_folder():
    """
    Return the exports directory path and create it if needed.

    Files are stored under backend/exports/ (see Config.EXPORT_FOLDER).
    """
    from flask import current_app

    folder = current_app.config["EXPORT_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    return folder


def make_student_filename(student_id):
    """Build filename: student_<id>_<timestamp>.csv"""
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"student_{student_id}_{stamp}.csv"


def make_company_drive_filename(drive_id):
    """Build filename: company_drive_<id>_<timestamp>.csv"""
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"company_drive_{drive_id}_{stamp}.csv"


def _final_result(status):
    """Show Selected / Rejected as final result; otherwise leave blank."""
    if status in ("Selected", "Rejected"):
        return status
    return ""


def write_student_applications_csv(student_id, filename):
    """
    Write one student's application history to a CSV file.

    Columns:
      Application ID, Drive Title, Company, Applied Date,
      Current Status, Interview Date, Interview Mode, Final Result
    """
    export_folder = get_export_folder()
    file_path = os.path.join(export_folder, filename)

    applications = (
        Application.query.filter_by(student_id=student_id)
        .order_by(Application.application_date.desc())
        .all()
    )

    headers = [
        "Application ID",
        "Drive Title",
        "Company",
        "Applied Date",
        "Current Status",
        "Interview Date",
        "Interview Mode",
        "Final Result",
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

        for app in applications:
            drive = app.drive
            company_name = ""
            drive_title = ""
            if drive:
                drive_title = drive.job_title or ""
                if drive.company:
                    company_name = drive.company.company_name or ""

            writer.writerow([
                app.id,
                drive_title,
                company_name,
                app.application_date.strftime("%Y-%m-%d %H:%M")
                if app.application_date
                else "",
                app.status or "",
                str(app.interview_date) if app.interview_date else "",
                app.interview_mode or "",
                _final_result(app.status),
            ])

    return file_path, len(applications)


def write_company_drive_csv(drive_id, filename):
    """
    Write all applicants for one placement drive to a CSV file.

    Columns:
      Student Name, Email, Branch, CGPA,
      Application Status, Interview Status, Selected
    """
    export_folder = get_export_folder()
    file_path = os.path.join(export_folder, filename)

    applications = (
        Application.query.filter_by(drive_id=drive_id)
        .order_by(Application.application_date.desc())
        .all()
    )

    headers = [
        "Student Name",
        "Email",
        "Branch",
        "CGPA",
        "Application Status",
        "Interview Status",
        "Selected",
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

        for app in applications:
            student = app.student
            name = student.full_name if student else ""
            email = student.user.email if student and student.user else ""
            branch = student.branch if student else ""
            cgpa = student.cgpa if student else ""

            # Interview Status: Scheduled if date exists, otherwise Not Scheduled
            if app.interview_date:
                interview_status = "Scheduled"
            else:
                interview_status = "Not Scheduled"

            selected = "Yes" if app.status == "Selected" else "No"

            writer.writerow([
                name,
                email,
                branch,
                cgpa,
                app.status or "",
                interview_status,
                selected,
            ])

    return file_path, len(applications)


def parse_drive_id_from_company_filename(filename):
    """
    Read drive id from company_drive_<id>_<timestamp>.csv.

    Returns drive_id as int, or None if the name is invalid.
    """
    # Example: company_drive_5_20260712_013000.csv
    if not filename.startswith("company_drive_"):
        return None
    if not filename.endswith(".csv"):
        return None

    parts = filename[:-4].split("_")
    # ["company", "drive", "<id>", "<date>", "<time>"]
    if len(parts) < 3:
        return None
    try:
        return int(parts[2])
    except ValueError:
        return None
