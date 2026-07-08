"""
company.py - Company Dashboard Routes

Protected routes for company users only.
Uses @company_required decorator for JWT role validation.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from decorators import company_required
from extensions import db
from models import Application, Company, PlacementDrive

company_bp = Blueprint("company", __name__)


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


@company_bp.route("/company/dashboard", methods=["GET"])
@company_required
def get_dashboard():
    """
    Company Dashboard API.

    Authentication flow:
      1. Frontend sends JWT in header: Authorization: Bearer <token>
      2. @company_required checks token is valid and role is "company"
      3. If checks pass, this function runs and returns dashboard data

    Returns company profile info and summary counts for the logged-in company.
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

    return jsonify({"message": "Placement drive closed successfully"}), 200
