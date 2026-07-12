"""
student.py - Student Dashboard + Profile Routes (Stages 6.1 / 6.2)

APIs
----
GET  /student/dashboard      - Overview cards + basic info (Stage 6.1)
GET  /student/profile        - Full profile for the edit page (Stage 6.2)
PUT  /student/profile        - Update editable profile fields (Stage 6.2)
POST /student/upload-resume  - Upload PDF resume, max 5 MB (Stage 6.2)

All routes require a valid Student JWT (@student_required).

Resume Upload Flow
------------------
1. Client sends multipart/form-data with a "resume" file field
2. Backend checks extension is .pdf
3. File is saved under backend/uploads/resumes/ with a unique name
4. student.resume_filename is updated in the database
5. Success JSON is returned
"""

import os
import uuid
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from cache_helpers import (
    CACHE_TIMEOUT,
    invalidate_admin_dashboard,
    invalidate_company_dashboard,
    invalidate_student_dashboard,
    invalidate_student_drives,
    student_dashboard_key,
    student_drives_key,
)
from decorators import student_required
from extensions import cache, db
from models import Application, Company, PlacementDrive, Student

student_bp = Blueprint("student", __name__)

# Allowed resume extension (PDF only)
ALLOWED_RESUME_EXTENSIONS = {"pdf"}


def _get_current_student():
    """
    Find the Student profile linked to the logged-in user.

    The JWT token stores user id (not student id).
    We use that id to look up the matching Student row.
    """
    user_id = int(get_jwt_identity())
    return Student.query.filter_by(user_id=user_id).first()


def _get_application_counts(student_id):
    """
    Count this student's applications using SQLAlchemy .count().

    Each query filters Application by student_id so a student
    only sees their own application statistics.
    """
    applied_drives = Application.query.filter_by(
        student_id=student_id
    ).count()

    selected_count = Application.query.filter_by(
        student_id=student_id,
        status="Selected",
    ).count()

    rejected_count = Application.query.filter_by(
        student_id=student_id,
        status="Rejected",
    ).count()

    return {
        "applied_drives": applied_drives,
        "selected_count": selected_count,
        "rejected_count": rejected_count,
    }


def _profile_to_dict(student):
    """Build a simple JSON-friendly dict from a Student row."""
    return {
        "full_name": student.full_name,
        "email": student.user.email,
        "phone": student.phone,
        "branch": student.branch,
        "cgpa": student.cgpa,
        "year": student.year,
        "skills": student.skills or "",
        "resume_filename": student.resume_filename,
    }


def _validate_profile_update(data):
    """
    Validate PUT /student/profile body.

    Checks:
    - full_name, phone required (non-empty)
    - cgpa required and between 0 and 10
    - skills is optional

    Returns (is_valid, error_message, cleaned_values).
    """
    if not data:
        return False, "Request body is required", None

    full_name = (data.get("full_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    skills = (data.get("skills") or "").strip()

    if not full_name:
        return False, "Full name is required", None

    if not phone:
        return False, "Phone is required", None

    # CGPA must be a number between 0 and 10
    try:
        cgpa = float(data.get("cgpa"))
    except (TypeError, ValueError):
        return False, "CGPA must be a valid number", None

    if cgpa < 0 or cgpa > 10:
        return False, "CGPA must be between 0 and 10", None

    cleaned = {
        "full_name": full_name,
        "phone": phone,
        "cgpa": cgpa,
        "skills": skills if skills else None,
    }
    return True, None, cleaned


def _is_allowed_resume(filename):
    """Return True if the filename ends with an allowed extension (.pdf)."""
    if not filename or "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_RESUME_EXTENSIONS


# ---------- Stage 7.2: Browse Approved Drives (no applying yet) ----------


def _get_query_param(name):
    """Read and strip a query parameter value."""
    value = request.args.get(name)
    return value.strip() if isinstance(value, str) else value


def _parse_int(value, field_name):
    """Parse integer query params with clear error messages."""
    if value is None or value == "":
        return None, None
    try:
        return int(value), None
    except (TypeError, ValueError):
        return None, f"{field_name} must be a valid number"


def _parse_float(value, field_name):
    """Parse float query params with clear error messages."""
    if value is None or value == "":
        return None, None
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, f"{field_name} must be a valid number"


def _format_drive_for_student(drive):
    """
    Build one drive entry for GET /student/drives (Stage 7.2).

    Returned fields:
      - Drive ID, Job Title, Company Name, Description
      - Eligible Branch, Minimum CGPA, Eligible Year, Deadline
    """
    return {
        "id": drive.id,
        "job_title": drive.job_title,
        "company_name": drive.company.company_name if drive.company else "",
        "description": drive.job_description,
        "eligible_branch": drive.eligible_branch,
        "minimum_cgpa": drive.minimum_cgpa,
        "eligible_year": drive.eligible_year,
        "status": drive.status,
        "deadline": drive.application_deadline.isoformat()
        if drive.application_deadline
        else None,
        "created_at": drive.created_at.isoformat() if drive.created_at else None,
    }


def _normalize_branch_list(branch_text):
    """
    Convert eligible_branch text like "CSE, ECE" into a normalized list:
    ["CSE", "ECE"] (uppercase, trimmed).
    """
    if not branch_text:
        return []
    parts = [p.strip().upper() for p in str(branch_text).split(",")]
    return [p for p in parts if p]


def _student_is_eligible(student, drive):
    """
    Eligibility checks:
    - Branch must be listed in drive.eligible_branch
    - CGPA must be >= drive.minimum_cgpa
    - Year must match drive.eligible_year
    """
    eligible_branches = _normalize_branch_list(drive.eligible_branch)
    student_branch = (student.branch or "").strip().upper()
    if eligible_branches and student_branch not in eligible_branches:
        return False, "You are not eligible for this drive (branch mismatch)"

    if student.cgpa < float(drive.minimum_cgpa):
        return False, "You are not eligible for this drive (CGPA too low)"

    if int(student.year) != int(drive.eligible_year):
        return False, "You are not eligible for this drive (year mismatch)"

    return True, None


def _deadline_has_passed(drive):
    """Return True if application_deadline is in the past."""
    if not drive.application_deadline:
        return False
    return drive.application_deadline < datetime.utcnow()


@student_bp.route("/student/drives", methods=["GET"])
@student_required
@cache.cached(timeout=CACHE_TIMEOUT, key_prefix=student_drives_key)
def browse_approved_drives():
    """
    GET /student/drives (Stage 7.2)

    Validation:
      - Only Student users can access (@student_required).

    Search (optional query params):
      - job_title, company_name, branch

    Filtering (optional query params):
      - branch, year, minimum_cgpa

    Notes:
      - Returns ONLY drives where status == "Approved"
      - Sorted by newest first (created_at DESC)
      - Also returns already_applied so the UI can disable Apply

    Stage 9.1: cached in Redis for 300 seconds.
    This endpoint is also the company / job search API
    (query params company_name, job_title, branch, year, minimum_cgpa).
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    job_title = _get_query_param("job_title")
    company_name = _get_query_param("company_name")
    branch = _get_query_param("branch")

    year, year_error = _parse_int(_get_query_param("year"), "year")
    if year_error:
        return jsonify({"message": year_error}), 400

    min_cgpa, cgpa_error = _parse_float(_get_query_param("minimum_cgpa"), "minimum_cgpa")
    if cgpa_error:
        return jsonify({"message": cgpa_error}), 400

    query = PlacementDrive.query.join(Company).filter(PlacementDrive.status == "Approved")

    # Search: simple "contains" matching using ilike (case-insensitive)
    if job_title:
        query = query.filter(PlacementDrive.job_title.ilike(f"%{job_title}%"))
    if company_name:
        query = query.filter(Company.company_name.ilike(f"%{company_name}%"))

    # Branch is stored as text (sometimes comma-separated), so we use "contains"
    if branch:
        query = query.filter(PlacementDrive.eligible_branch.ilike(f"%{branch}%"))

    # Filters: exact year, and drives whose minimum CGPA requirement is <= given CGPA
    if year is not None:
        query = query.filter(PlacementDrive.eligible_year == year)
    if min_cgpa is not None:
        query = query.filter(PlacementDrive.minimum_cgpa <= min_cgpa)

    drives = query.order_by(PlacementDrive.created_at.desc()).all()

    # Build a set of drive_ids already applied by this student (for UX)
    drive_ids = [d.id for d in drives]
    applied_ids = set()
    if drive_ids:
        rows = Application.query.filter(
            Application.student_id == student.id,
            Application.drive_id.in_(drive_ids),
        ).all()
        applied_ids = {r.drive_id for r in rows}

    result = []
    for d in drives:
        row = _format_drive_for_student(d)
        row["already_applied"] = d.id in applied_ids
        result.append(row)

    return jsonify(result), 200


# ---------- Stage 7 Combined: Student Apply + My Applications ----------


@student_bp.route("/student/apply/<int:drive_id>", methods=["POST"])
@student_required
def apply_to_drive(drive_id):
    """
    POST /student/apply/<drive_id>

    Rules:
    - Student can apply only once
    - Drive must be Approved (not Pending/Rejected/Closed)
    - Deadline must not have passed
    - Student must satisfy branch, CGPA, year
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"message": "Placement drive not found"}), 404

    if drive.status != "Approved":
        return jsonify({"message": "You can apply only to approved drives"}), 400

    if _deadline_has_passed(drive):
        return jsonify({"message": "Application deadline has passed"}), 400

    # Prevent duplicates
    existing = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive.id,
    ).first()
    if existing:
        return jsonify({"message": "You have already applied to this drive"}), 400

    eligible, reason = _student_is_eligible(student, drive)
    if not eligible:
        return jsonify({"message": reason}), 400

    application = Application(
        student_id=student.id,
        drive_id=drive.id,
        status="Applied",
        application_date=datetime.utcnow(),
    )
    db.session.add(application)
    db.session.commit()

    # Stage 9.1: apply itself is not cached; refresh related dashboards / search
    invalidate_admin_dashboard()
    invalidate_student_dashboard(student.user_id)
    invalidate_student_drives()
    if drive.company:
        invalidate_company_dashboard(drive.company.user_id)

    return jsonify({"message": "Application submitted successfully"}), 201


def _format_application_row(app):
    """Return one application row for GET /student/applications."""
    drive = app.drive
    company_name = drive.company.company_name if drive and drive.company else ""
    return {
        "id": app.id,
        "drive_id": app.drive_id,
        "job_title": drive.job_title if drive else "",
        "company_name": company_name,
        "applied_date": app.application_date.isoformat() if app.application_date else None,
        "status": app.status,
        "interview_date": app.interview_date.isoformat() if app.interview_date else None,
        "interview_time": app.interview_time,
        "interview_mode": app.interview_mode,
    }


@student_bp.route("/student/applications", methods=["GET"])
@student_required
def get_my_applications():
    """
    GET /student/applications

    Return ONLY the logged-in student's applications.
    Sorted: newest first (application_date DESC).

    Status values used in the UI:
    Applied, Shortlisted, Interview, Selected, Rejected
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    apps = (
        Application.query.filter_by(student_id=student.id)
        .order_by(Application.application_date.desc())
        .all()
    )

    return jsonify([_format_application_row(a) for a in apps]), 200


# ---------- Stage 6.1: Dashboard ----------


@student_bp.route("/student/dashboard", methods=["GET"])
@student_required
@cache.cached(timeout=CACHE_TIMEOUT, key_prefix=student_dashboard_key)
def get_dashboard():
    """
    GET /student/dashboard

    Returns student profile + overview counts for the Student Dashboard.

    Stage 9.1: response cached in Redis for 300 seconds (per student user).
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    available_drives = PlacementDrive.query.filter_by(
        status="Approved"
    ).count()

    app_counts = _get_application_counts(student.id)
    resume_uploaded = "Yes" if student.resume_filename else "No"

    return jsonify({
        "full_name": student.full_name,
        "email": student.user.email,
        "branch": student.branch,
        "cgpa": student.cgpa,
        "year": student.year,
        "resume_uploaded": resume_uploaded,
        "available_drives": available_drives,
        "applied_drives": app_counts["applied_drives"],
        "selected_count": app_counts["selected_count"],
        "rejected_count": app_counts["rejected_count"],
    }), 200


# ---------- Stage 6.2: Profile ----------


@student_bp.route("/student/profile", methods=["GET"])
@student_required
def get_profile():
    """
    GET /student/profile

    Return the logged-in student's full profile for the Profile page.

    Branch and Year are included but treated as read-only on the frontend.
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    return jsonify(_profile_to_dict(student)), 200


@student_bp.route("/student/profile", methods=["PUT"])
@student_required
def update_profile():
    """
    PUT /student/profile

    Update editable fields: full_name, phone, cgpa, skills.
    Branch, year, and email cannot be changed here.
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    data = request.get_json(silent=True)
    is_valid, error_message, cleaned = _validate_profile_update(data)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    # Apply validated values to the Student row
    student.full_name = cleaned["full_name"]
    student.phone = cleaned["phone"]
    student.cgpa = cleaned["cgpa"]
    student.skills = cleaned["skills"]

    db.session.commit()

    # Stage 9.1: dashboard shows name / CGPA from profile
    invalidate_student_dashboard(student.user_id)
    invalidate_admin_dashboard()

    return jsonify({
        "message": "Profile updated successfully",
        "profile": _profile_to_dict(student),
    }), 200


@student_bp.route("/student/upload-resume", methods=["POST"])
@student_required
def upload_resume():
    """
    POST /student/upload-resume

    Accept a PDF file (field name: "resume"), max 5 MB.
    Save it under backend/uploads/resumes/ and store the filename in DB.

    Request must be multipart/form-data (not JSON).
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    # Step 1: Check a file was sent under the "resume" key
    if "resume" not in request.files:
        return jsonify({"message": "No resume file provided"}), 400

    file = request.files["resume"]

    if not file or file.filename == "":
        return jsonify({"message": "No resume file selected"}), 400

    # Step 2: Reject non-PDF uploads
    if not _is_allowed_resume(file.filename):
        return jsonify({"message": "Only PDF files are allowed"}), 400

    # Step 3: Build a safe, unique filename
    # secure_filename removes unsafe path characters
    original_name = secure_filename(file.filename)
    unique_name = f"{student.id}_{uuid.uuid4().hex}_{original_name}"

    # Step 4: Ensure upload folder exists and save the file
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_name)
    file.save(file_path)

    # Step 5: Store filename in the database
    student.resume_filename = unique_name
    db.session.commit()

    # Stage 9.1: dashboard shows resume_uploaded Yes/No
    invalidate_student_dashboard(student.user_id)

    return jsonify({
        "message": "Resume uploaded successfully",
        "resume_filename": unique_name,
    }), 200


# ---------- Stage 9.5: Async CSV Export ----------


@student_bp.route("/student/export", methods=["POST"])
@student_required
def export_applications():
    """
    POST /student/export

    Queue a Celery job that writes this student's applications to CSV.
    Returns task_id, status, and the filename that will be created.
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    from services.export_service import make_student_filename
    from tasks import export_student_csv

    filename = make_student_filename(student.id)
    async_result = export_student_csv.delay(student.id, filename)

    return jsonify({
        "task_id": async_result.id,
        "status": async_result.status,
        "filename": filename,
    }), 200


@student_bp.route("/student/export/download/<path:filename>", methods=["GET"])
@student_required
def download_student_export(filename):
    """
    GET /student/export/download/<filename>

    Download a CSV only if it belongs to the logged-in student.
    Filename must look like: student_<student_id>_....csv
    """
    student = _get_current_student()
    if not student:
        return jsonify({"message": "Student profile not found"}), 404

    # Block path tricks (../ etc.)
    safe_name = secure_filename(filename)
    if safe_name != filename or not safe_name.endswith(".csv"):
        return jsonify({"message": "Invalid filename"}), 400

    # Ownership: only this student's exports
    expected_prefix = f"student_{student.id}_"
    if not safe_name.startswith(expected_prefix):
        return jsonify({"message": "You can only download your own exports"}), 403

    export_folder = current_app.config["EXPORT_FOLDER"]
    file_path = os.path.join(export_folder, safe_name)

    if not os.path.isfile(file_path):
        return jsonify({"message": "Export not ready yet"}), 404

    real_export = os.path.realpath(export_folder)
    real_file = os.path.realpath(file_path)
    if not real_file.startswith(real_export + os.sep):
        return jsonify({"message": "Invalid file path"}), 400

    return send_from_directory(export_folder, safe_name, as_attachment=True)
