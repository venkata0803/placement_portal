"""
company.py - Company Dashboard Routes

Protected routes for company users only.
Uses @company_required decorator for JWT role validation.
"""

from datetime import datetime
import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from cache_helpers import (
    CACHE_TIMEOUT,
    company_dashboard_key,
    invalidate_admin_dashboard,
    invalidate_after_drive_status_change,
    invalidate_all_student_dashboards,
    invalidate_company_dashboard,
    invalidate_student_dashboard,
    invalidate_student_drives,
)
from decorators import company_required
from extensions import cache, db
from models import Application, Company, PlacementDrive

company_bp = Blueprint("company", __name__)

# Allowed application statuses for company applicant management (Stage 8)
ALLOWED_STATUSES = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]
ALLOWED_INTERVIEW_MODES = ["Online", "Offline"]


def _get_current_company():
    """
    Find the Company profile linked to the logged-in user.

    The JWT token stores user id (not company id).
    We use that id to look up the matching Company row.
    """
    user_id = int(get_jwt_identity())
    return Company.query.filter_by(user_id=user_id).first()


def _get_drive_counts(company_id):
    """
    Count placement drives for one company using SQLAlchemy .count().

    Each query filters PlacementDrive by company_id so a company
    only sees its own drives, not drives from other companies.
    """
    total_placement_drives = PlacementDrive.query.filter_by(
        company_id=company_id
    ).count()

    approved_drives = PlacementDrive.query.filter_by(
        company_id=company_id,
        status="Approved",
    ).count()

    pending_drives = PlacementDrive.query.filter_by(
        company_id=company_id,
        status="Pending",
    ).count()

    return {
        "total_placement_drives": total_placement_drives,
        "approved_drives": approved_drives,
        "pending_drives": pending_drives,
    }


def _get_application_count(company_id):
    """
    Count all applications received on this company's drives.

    We join Application with PlacementDrive because applications
    are linked to a drive, and each drive belongs to one company.
    """
    return (
        Application.query.join(PlacementDrive)
        .filter(PlacementDrive.company_id == company_id)
        .count()
    )


def _check_company_approval(company):
    """
    Only approved companies can create or view placement drives.

    Returns (None, None) if approved.
    Returns (json_response, status_code) if access should be blocked.
    """
    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    if company.approval_status == "Rejected":
        return jsonify({"message": "Company registration rejected."}), 403

    if company.approval_status != "Approved":
        return jsonify({"message": "Company approval pending."}), 403

    return None, None


def _validate_drive_data(data):
    """
    Validate placement drive input from POST /company/drives.

    Checks required fields, CGPA range (0-10), and deadline not in past.
    Returns (is_valid, error_message, parsed_values).
    """
    required_fields = [
        "job_title",
        "job_description",
        "eligible_branch",
        "minimum_cgpa",
        "eligible_year",
        "application_deadline",
    ]

    for field_name in required_fields:
        field_value = data.get(field_name)
        if field_value is None or field_value == "":
            return False, f"{field_name} is required", None

    try:
        minimum_cgpa = float(data.get("minimum_cgpa"))
    except (TypeError, ValueError):
        return False, "minimum_cgpa must be a number", None

    if minimum_cgpa < 0 or minimum_cgpa > 10:
        return False, "minimum_cgpa must be between 0 and 10", None

    try:
        eligible_year = int(data.get("eligible_year"))
    except (TypeError, ValueError):
        return False, "eligible_year must be a number", None

    if eligible_year < 1 or eligible_year > 4:
        return False, "eligible_year must be between 1 and 4", None

    deadline_string = data.get("application_deadline")
    try:
        application_deadline = datetime.fromisoformat(deadline_string)
    except (TypeError, ValueError):
        return False, "application_deadline must be a valid date", None

    if application_deadline.date() < datetime.utcnow().date():
        return False, "application_deadline cannot be in the past", None

    parsed_values = {
        "job_title": str(data.get("job_title")).strip(),
        "job_description": str(data.get("job_description")).strip(),
        "eligible_branch": str(data.get("eligible_branch")).strip(),
        "minimum_cgpa": minimum_cgpa,
        "eligible_year": eligible_year,
        "application_deadline": application_deadline,
    }

    return True, None, parsed_values


def _format_company_drive_row(drive):
    """Build one drive entry for GET /company/drives response."""
    return {
        "id": drive.id,
        "title": drive.job_title,
        # Included so the Edit modal can pre-fill the description field
        "job_description": drive.job_description,
        "eligible_branch": drive.eligible_branch,
        "minimum_cgpa": drive.minimum_cgpa,
        "eligible_year": drive.eligible_year,
        "deadline": drive.application_deadline.isoformat()
        if drive.application_deadline
        else None,
        "status": drive.status,
        "created_at": drive.created_at.isoformat() if drive.created_at else None,
    }


def _get_owned_drive(company, drive_id):
    """
    Find a placement drive that belongs to this company.

    Ownership rule: drive.company_id must match the logged-in company.
    Returns the drive, or None if not found / not owned.
    """
    return PlacementDrive.query.filter_by(
        id=drive_id,
        company_id=company.id,
    ).first()


def _get_owned_application(company, application_id):
    """
    Find an application that belongs to one of this company's drives.

    Ownership rule: Application → PlacementDrive → company_id must match.
    Returns the application, or None if not found / not owned.
    """
    return (
        Application.query.join(PlacementDrive)
        .filter(
            Application.id == application_id,
            PlacementDrive.company_id == company.id,
        )
        .first()
    )


def _format_application_row(app):
    """
    Build one applicant row for GET /company/drives/<drive_id>/applications.

    Joins student + user data so the company can review each applicant.
    """
    student = app.student
    user = student.user if student else None

    return {
        "id": app.id,
        "student_name": student.full_name if student else "",
        "email": user.email if user else "",
        "branch": student.branch if student else "",
        "cgpa": student.cgpa if student else None,
        "year": student.year if student else None,
        "skills": student.skills if student else "",
        "resume_filename": student.resume_filename if student else "",
        "status": app.status,
        "applied_date": app.application_date.isoformat()
        if app.application_date
        else None,
        "interview_date": app.interview_date.isoformat()
        if app.interview_date
        else None,
        "interview_time": app.interview_time,
        "interview_mode": app.interview_mode,
    }


def _validate_status_change(application, new_status):
    """
    Status flow rules (Stage 8):
      - Rejected applications cannot be edited
      - Selected cannot be changed back to Applied (or any earlier stage)
      - Interview status is allowed only after Shortlisted
    """
    current_status = application.status

    if current_status == "Rejected":
        return False, "Rejected applications cannot be edited."

    if current_status == "Selected" and new_status != "Selected":
        return False, "Selected applications cannot be changed."

    if current_status == "Selected" and new_status == "Applied":
        return False, "Cannot change Selected back to Applied."

    if new_status == "Interview":
        return (
            False,
            "Interview status requires scheduling interview details. Use the interview endpoint.",
        )

    return True, None


@company_bp.route("/company/dashboard", methods=["GET"])
@company_required
@cache.cached(timeout=CACHE_TIMEOUT, key_prefix=company_dashboard_key)
def get_dashboard():
    """
    Company Dashboard API.

    Authentication flow:
      1. Frontend sends JWT in header: Authorization: Bearer <token>
      2. @company_required checks token is valid and role is "company"
      3. If checks pass, this function runs and returns dashboard data

    Returns company profile info and summary counts for the logged-in company.

    Stage 9.1: response cached in Redis for 300 seconds (per company user).
    """
    company = _get_current_company()

    if not company:
        return jsonify({"message": "Company profile not found"}), 404

    drive_counts = _get_drive_counts(company.id)
    total_applications = _get_application_count(company.id)

    return jsonify({
        "company_name": company.company_name,
        "website": company.website,
        "hr_name": company.hr_name,
        "hr_email": company.hr_email,
        "approval_status": company.approval_status,
        "total_placement_drives": drive_counts["total_placement_drives"],
        "approved_drives": drive_counts["approved_drives"],
        "pending_drives": drive_counts["pending_drives"],
        "total_applications": total_applications,
    }), 200


@company_bp.route("/company/drives", methods=["GET"])
@company_required
def get_company_drives():
    """
    List placement drives for the logged-in company.

    Authentication:
      1. @company_required ensures JWT is valid and role is "company"
      2. _check_company_approval ensures company is Approved

    Returns only drives where company_id matches the logged-in company.
    Sorted by created_at descending (newest first).
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    company_drives = (
        PlacementDrive.query.filter_by(company_id=company.id)
        .order_by(PlacementDrive.created_at.desc())
        .all()
    )

    drive_list = [_format_company_drive_row(drive) for drive in company_drives]
    return jsonify(drive_list), 200


@company_bp.route("/company/drives", methods=["POST"])
@company_required
def create_company_drive():
    """
    Create a new placement drive for the logged-in company.

    Drive creation flow:
      1. Verify company is Approved
      2. Validate all input fields
      3. Set company_id from logged-in company (not from request body)
      4. Set status = "Pending" and created_at automatically
      5. Save to database and return success message
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    request_data = request.get_json(silent=True) or {}
    is_valid, error_message, parsed_values = _validate_drive_data(request_data)

    if not is_valid:
        return jsonify({"message": error_message}), 400

    new_drive = PlacementDrive(
        company_id=company.id,
        job_title=parsed_values["job_title"],
        job_description=parsed_values["job_description"],
        eligible_branch=parsed_values["eligible_branch"],
        minimum_cgpa=parsed_values["minimum_cgpa"],
        eligible_year=parsed_values["eligible_year"],
        application_deadline=parsed_values["application_deadline"],
        status="Pending",
    )

    db.session.add(new_drive)
    db.session.commit()

    # Stage 9.1: new Pending drive changes admin + company dashboard counts
    invalidate_admin_dashboard()
    invalidate_company_dashboard(company.user_id)

    return jsonify({"message": "Placement drive created successfully"}), 201


@company_bp.route("/company/drives/<int:drive_id>", methods=["PUT"])
@company_required
def update_company_drive(drive_id):
    """
    Update an existing placement drive (Stage 5.3).

    Edit workflow:
      1. @company_required → only company users
      2. Company must be Approved
      3. Drive must belong to this company (owner check)
      4. Closed drives cannot be edited
      5. Reuse _validate_drive_data for fields / CGPA / deadline
      6. Save updates and return success message

    Validation (same as create):
      - Deadline cannot be in the past
      - CGPA must be between 0 and 10
      - All fields are required
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    # Ownership: only the company that created the drive can update it
    drive = _get_owned_drive(company, drive_id)
    if not drive:
        return jsonify({"message": "Placement drive not found"}), 404

    # Closed drives are locked — no further edits allowed
    if drive.status == "Closed":
        return jsonify({"message": "Closed drives cannot be edited"}), 400

    request_data = request.get_json(silent=True) or {}
    is_valid, error_message, parsed_values = _validate_drive_data(request_data)

    if not is_valid:
        return jsonify({"message": error_message}), 400

    # Apply validated values to the existing drive row
    drive.job_title = parsed_values["job_title"]
    drive.job_description = parsed_values["job_description"]
    drive.eligible_branch = parsed_values["eligible_branch"]
    drive.minimum_cgpa = parsed_values["minimum_cgpa"]
    drive.eligible_year = parsed_values["eligible_year"]
    drive.application_deadline = parsed_values["application_deadline"]

    db.session.commit()

    # Stage 9.1: Approved drives appear in student search — refresh those caches
    if drive.status == "Approved":
        invalidate_student_drives()
        invalidate_all_student_dashboards()

    return jsonify({"message": "Placement drive updated successfully"}), 200


@company_bp.route("/company/drives/<int:drive_id>/close", methods=["PATCH"])
@company_required
def close_company_drive(drive_id):
    """
    Close a placement drive (Stage 5.3).

    Close workflow:
      1. @company_required → only company users
      2. Company must be Approved
      3. Drive must belong to this company (owner check)
      4. If already Closed → return a clear message
      5. Otherwise set status = "Closed" and save

    Does NOT delete the drive — only changes status.
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    # Ownership: only the company that created the drive can close it
    drive = _get_owned_drive(company, drive_id)
    if not drive:
        return jsonify({"message": "Placement drive not found"}), 404

    # Already closed — return an informative message (not an error crash)
    if drive.status == "Closed":
        return jsonify({"message": "Placement drive is already closed"}), 400

    drive.status = "Closed"
    db.session.commit()

    # Stage 9.1: closed drives leave student search / dashboards
    invalidate_after_drive_status_change(company.user_id)

    return jsonify({"message": "Placement drive closed successfully"}), 200


# ---------- Stage 8: Company Applicant Management ----------


@company_bp.route("/company/drives/<int:drive_id>/applications", methods=["GET"])
@company_required
def get_drive_applications(drive_id):
    """
    List applicants for one placement drive owned by the logged-in company.

    Applicant flow:
      1. Student applies to an approved drive → status = Applied
      2. Company opens this page → sees all applications for that drive
      3. Company shortlists, schedules interview, selects, or rejects
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    # Only the company that owns the drive can view its applicants
    drive = _get_owned_drive(company, drive_id)
    if not drive:
        return jsonify({"message": "Placement drive not found"}), 404

    applications = (
        Application.query.filter_by(drive_id=drive_id)
        .order_by(Application.application_date.desc())
        .all()
    )

    applicant_list = [_format_application_row(app) for app in applications]
    return jsonify(applicant_list), 200


@company_bp.route("/company/application/<int:application_id>/status", methods=["PUT"])
@company_required
def update_application_status(application_id):
    """
    Update an applicant's status.

    Allowed values: Applied, Shortlisted, Interview, Selected, Rejected
    Only the company that owns the drive may update.
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    application = _get_owned_application(company, application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    request_data = request.get_json(silent=True) or {}
    new_status = request_data.get("status")

    if not new_status:
        return jsonify({"message": "status is required"}), 400

    if new_status not in ALLOWED_STATUSES:
        return jsonify({
            "message": f"Invalid status. Allowed values: {', '.join(ALLOWED_STATUSES)}"
        }), 400

    is_valid, error_message = _validate_status_change(application, new_status)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    application.status = new_status
    db.session.commit()

    # Stage 9.1: student dashboard selected/rejected counts may change
    if application.student:
        invalidate_student_dashboard(application.student.user_id)

    return jsonify({"message": "Application status updated successfully"}), 200


@company_bp.route("/company/application/<int:application_id>/interview", methods=["PUT"])
@company_required
def schedule_application_interview(application_id):
    """
    Schedule or update interview details for a shortlisted applicant.

    Interview flow:
      1. Company shortlists the student (status = Shortlisted)
      2. Company opens Interview modal → enters date, time, mode
      3. Backend stores details and sets status = Interview

    Validation: interview can be scheduled only after Shortlisted.
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    application = _get_owned_application(company, application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    if application.status == "Rejected":
        return jsonify({"message": "Rejected applications cannot be edited."}), 400

    if application.status == "Selected":
        return jsonify({"message": "Selected applications cannot be edited."}), 400

    # Interview is allowed only after the student has been shortlisted
    if application.status not in ("Shortlisted", "Interview"):
        return jsonify({
            "message": "Interview can be scheduled only after the student is Shortlisted."
        }), 400

    request_data = request.get_json(silent=True) or {}
    interview_date_str = request_data.get("interview_date")
    interview_time = request_data.get("interview_time")
    interview_mode = request_data.get("interview_mode")

    if not interview_date_str or not interview_time or not interview_mode:
        return jsonify({
            "message": "interview_date, interview_time, and interview_mode are required"
        }), 400

    if interview_mode not in ALLOWED_INTERVIEW_MODES:
        return jsonify({
            "message": f"interview_mode must be one of: {', '.join(ALLOWED_INTERVIEW_MODES)}"
        }), 400

    try:
        interview_date = datetime.strptime(interview_date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return jsonify({"message": "interview_date must be YYYY-MM-DD"}), 400

    application.interview_date = interview_date
    application.interview_time = str(interview_time).strip()
    application.interview_mode = interview_mode
    application.status = "Interview"

    db.session.commit()

    # Stage 9.1: student application status changed (dashboard stats)
    if application.student:
        invalidate_student_dashboard(application.student.user_id)

    return jsonify({"message": "Interview scheduled successfully"}), 200


@company_bp.route("/company/application/<int:application_id>/resume", methods=["GET"])
@company_required
def download_application_resume(application_id):
    """
    Download a student's resume PDF for an application on this company's drive.

    Security:
      - Company must own the placement drive linked to the application
      - Only PDF files stored in the upload folder are served
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    application = _get_owned_application(company, application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    student = application.student
    if not student or not student.resume_filename:
        return jsonify({"message": "Resume not uploaded"}), 404

    filename = student.resume_filename
    if not filename.lower().endswith(".pdf"):
        return jsonify({"message": "Only PDF resumes can be downloaded"}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    if not os.path.isfile(file_path):
        return jsonify({"message": "Resume file not found"}), 404

    real_upload = os.path.realpath(upload_folder)
    real_file = os.path.realpath(file_path)
    if not real_file.startswith(real_upload + os.sep):
        return jsonify({"message": "Invalid file path"}), 400

    return send_from_directory(upload_folder, filename, as_attachment=True)


# ---------- Stage 9.5: Async CSV Export ----------


@company_bp.route("/company/export/<int:drive_id>", methods=["POST"])
@company_required
def export_drive_applicants(drive_id):
    """
    POST /company/export/<drive_id>

    Queue a Celery job that writes applicants for one owned drive to CSV.
    Returns task_id, status, and the filename that will be created.
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    # Security: company may export only its own drives
    drive = _get_owned_drive(company, drive_id)
    if not drive:
        return jsonify({"message": "Placement drive not found"}), 404

    from services.export_service import make_company_drive_filename
    from tasks import export_company_csv

    filename = make_company_drive_filename(drive.id)
    async_result = export_company_csv.delay(drive.id, filename)

    return jsonify({
        "task_id": async_result.id,
        "status": async_result.status,
        "filename": filename,
    }), 200


@company_bp.route("/company/export/download/<path:filename>", methods=["GET"])
@company_required
def download_company_export(filename):
    """
    GET /company/export/download/<filename>

    Download a CSV only if it belongs to a drive owned by this company.
    Filename must look like: company_drive_<drive_id>_....csv
    """
    company = _get_current_company()
    error_response, status_code = _check_company_approval(company)
    if error_response:
        return error_response, status_code

    safe_name = secure_filename(filename)
    if safe_name != filename or not safe_name.endswith(".csv"):
        return jsonify({"message": "Invalid filename"}), 400

    from services.export_service import parse_drive_id_from_company_filename

    drive_id = parse_drive_id_from_company_filename(safe_name)
    if drive_id is None:
        return jsonify({"message": "Invalid export filename"}), 400

    # Ownership: drive must belong to this company
    drive = _get_owned_drive(company, drive_id)
    if not drive:
        return jsonify({"message": "You can only download exports for your own drives"}), 403

    export_folder = current_app.config["EXPORT_FOLDER"]
    file_path = os.path.join(export_folder, safe_name)

    if not os.path.isfile(file_path):
        return jsonify({"message": "Export not ready yet"}), 404

    real_export = os.path.realpath(export_folder)
    real_file = os.path.realpath(file_path)
    if not real_file.startswith(real_export + os.sep):
        return jsonify({"message": "Invalid file path"}), 400

    return send_from_directory(export_folder, safe_name, as_attachment=True)
