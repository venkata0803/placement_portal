"""
admin.py - Admin Dashboard Routes

Protected routes for admin users only.
Uses @admin_required decorator for JWT role validation.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from cache_helpers import (
    CACHE_TIMEOUT,
    admin_dashboard_key,
    invalidate_admin_dashboard,
    invalidate_after_drive_status_change,
    invalidate_company_dashboard,
    invalidate_student_dashboard,
    with_cache_performance_log,
)
from decorators import admin_required
from extensions import cache, db
from models import Application, Company, PlacementDrive, Student, User

admin_bp = Blueprint("admin", __name__)


def _get_total_counts():
    """
    Count total rows in each main table.
    Simple SQLAlchemy .count() queries for dashboard summary cards.
    """
    return {
        "total_students": Student.query.count(),
        "total_companies": Company.query.count(),
        "total_placement_drives": PlacementDrive.query.count(),
        "total_applications": Application.query.count(),
    }


def _format_user_row(name, email, created_at):
    """Build one recent user entry for the JSON response."""
    return {
        "name": name,
        "email": email,
        "created_at": created_at.isoformat() if created_at else None,
    }


def _get_recent_students():
    """
    Fetch the 5 most recently registered students.
    Sorted by User.created_at descending (newest first).
    """
    recent_students = (
        Student.query.join(User)
        .filter(User.role == "student")
        .order_by(User.created_at.desc())
        .limit(5)
        .all()
    )

    return [
        _format_user_row(student.full_name, student.user.email, student.user.created_at)
        for student in recent_students
    ]


def _get_recent_companies():
    """
    Fetch the 5 most recently registered companies.
    Sorted by User.created_at descending (newest first).
    """
    recent_companies = (
        Company.query.join(User)
        .filter(User.role == "company")
        .order_by(User.created_at.desc())
        .limit(5)
        .all()
    )

    return [
        _format_user_row(
            company.company_name, company.user.email, company.user.created_at
        )
        for company in recent_companies
    ]


@admin_bp.route("/admin/dashboard", methods=["GET"])
@admin_required
@with_cache_performance_log("admin_dashboard", admin_dashboard_key)
@cache.cached(timeout=CACHE_TIMEOUT, key_prefix=admin_dashboard_key)
def get_dashboard():
    """
    Admin Dashboard API.

    Returns summary counts and recent student/company registrations.
    Only accessible by users with role "admin" in their JWT token.

    Stage 9.1: response cached in Redis for 300 seconds.
    """
    counts = _get_total_counts()

    return jsonify({
        **counts,
        "recent_students": _get_recent_students(),
        "recent_companies": _get_recent_companies(),
    }), 200


def _format_company_row(company):
    """Build one company entry for the admin companies list."""
    return {
        "id": company.id,
        "company_name": company.company_name,
        "email": company.user.email,
        "website": company.website or "",
        "industry": company.industry or "",
        "location": company.location or "",
        "approval_status": company.approval_status,
        "is_blacklisted": company.is_blacklisted,
        "created_at": company.user.created_at.isoformat()
        if company.user.created_at
        else None,
    }


def _format_student_row(student):
    """Build one student entry for the admin students list."""
    return {
        "id": student.id,
        "full_name": student.full_name,
        "email": student.user.email,
        "branch": student.branch,
        "year": student.year,
        "cgpa": student.cgpa,
        "is_blacklisted": student.is_blacklisted,
        "created_at": student.user.created_at.isoformat()
        if student.user.created_at
        else None,
    }


def _format_application_admin_row(application):
    """
    Build one application entry for GET /admin/applications.

    Final Result: Selected / Rejected when decided; otherwise Pending.
    """
    student = application.student
    drive = application.drive
    company = drive.company if drive else None

    status = application.status or "Applied"
    if status in ("Selected", "Rejected"):
        final_result = status
    else:
        final_result = "Pending"

    return {
        "id": application.id,
        "student_name": student.full_name if student else "",
        "student_email": student.user.email if student and student.user else "",
        "company": company.company_name if company else "",
        "drive": drive.job_title if drive else "",
        "applied_date": application.application_date.isoformat()
        if application.application_date
        else None,
        "status": status,
        "interview_date": application.interview_date.isoformat()
        if application.interview_date
        else None,
        "interview_mode": application.interview_mode,
        "final_result": final_result,
    }


def _format_drive_row(drive):
    """
    Build one placement drive entry for the admin drives list (Stage 7.1).

    Contract for GET /admin/drives:
      - Drive ID
      - Job Title
      - Company Name
      - Eligible Branch
      - Minimum CGPA
      - Eligible Year
      - Deadline
      - Status
      - Created Date
    """
    return {
        "id": drive.id,
        "job_title": drive.job_title,
        "company_name": drive.company.company_name if drive.company else "",
        "eligible_branch": drive.eligible_branch,
        "minimum_cgpa": drive.minimum_cgpa,
        "eligible_year": drive.eligible_year,
        "status": drive.status,
        "deadline": drive.application_deadline.isoformat()
        if drive.application_deadline
        else None,
        "created_at": drive.created_at.isoformat() if drive.created_at else None,
    }


@admin_bp.route("/admin/companies", methods=["GET"])
@admin_required
def get_all_companies():
    """
    Return companies for admin review, with optional backend search.

    Query params (all optional, case-insensitive contains):
      - company_name / name
      - industry
      - location
      - q  (matches company name, industry, or location)

    Without filters, returns the full list (backward compatible).
    """
    query = Company.query.join(User)

    company_name = (request.args.get("company_name") or request.args.get("name") or "").strip()
    industry = (request.args.get("industry") or "").strip()
    location = (request.args.get("location") or "").strip()
    free_text = (request.args.get("q") or request.args.get("search") or "").strip()

    if company_name:
        query = query.filter(Company.company_name.ilike(f"%{company_name}%"))
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    if location:
        query = query.filter(Company.location.ilike(f"%{location}%"))
    if free_text:
        like = f"%{free_text}%"
        query = query.filter(
            db.or_(
                Company.company_name.ilike(like),
                Company.industry.ilike(like),
                Company.location.ilike(like),
            )
        )

    companies = query.order_by(User.created_at.desc()).all()
    return jsonify([_format_company_row(company) for company in companies]), 200


@admin_bp.route("/admin/company/<int:company_id>/approve", methods=["PUT"])
@admin_required
def approve_company(company_id):
    """Set company approval_status to Approved."""
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    company.approval_status = "Approved"
    db.session.commit()

    # Stage 9.1: approval is not cached, but related dashboards must refresh
    invalidate_admin_dashboard()
    invalidate_company_dashboard(company.user_id)

    return jsonify({"message": "Company approved successfully"}), 200


@admin_bp.route("/admin/company/<int:company_id>/reject", methods=["PUT"])
@admin_required
def reject_company(company_id):
    """Set company approval_status to Rejected."""
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    company.approval_status = "Rejected"
    db.session.commit()

    invalidate_admin_dashboard()
    invalidate_company_dashboard(company.user_id)

    return jsonify({"message": "Company rejected successfully"}), 200


@admin_bp.route("/admin/company/<int:company_id>/blacklist", methods=["PUT"])
@admin_required
def blacklist_company(company_id):
    """Blacklist a company — blocks login and drive creation."""
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    if company.is_blacklisted:
        return jsonify({"message": "Company is already blacklisted"}), 400

    company.is_blacklisted = True
    db.session.commit()

    invalidate_admin_dashboard()
    invalidate_company_dashboard(company.user_id)

    return jsonify({"message": "Company blacklisted successfully"}), 200


@admin_bp.route("/admin/company/<int:company_id>/unblacklist", methods=["PUT"])
@admin_required
def unblacklist_company(company_id):
    """Remove a company from the blacklist (Activate)."""
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    if not company.is_blacklisted:
        return jsonify({"message": "Company is not blacklisted"}), 400

    company.is_blacklisted = False
    db.session.commit()

    invalidate_admin_dashboard()
    invalidate_company_dashboard(company.user_id)

    return jsonify({"message": "Company activated successfully"}), 200


@admin_bp.route("/admin/students", methods=["GET"])
@admin_required
def get_all_students():
    """
    Return students for admin review / blacklist management, with optional search.

    Query params (all optional, case-insensitive contains except year):
      - name / full_name
      - email
      - branch
      - year
      - q  (matches name, email, or branch)

    Without filters, returns the full list (backward compatible).
    """
    query = (
        Student.query.join(User)
        .filter(User.role == "student")
    )

    name = (request.args.get("name") or request.args.get("full_name") or "").strip()
    email = (request.args.get("email") or "").strip()
    branch = (request.args.get("branch") or "").strip()
    year = (request.args.get("year") or "").strip()
    free_text = (request.args.get("q") or request.args.get("search") or "").strip()

    if name:
        query = query.filter(Student.full_name.ilike(f"%{name}%"))
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))
    if branch:
        query = query.filter(Student.branch.ilike(f"%{branch}%"))
    if year:
        try:
            query = query.filter(Student.year == int(year))
        except ValueError:
            return jsonify({"message": "year must be a number"}), 400
    if free_text:
        like = f"%{free_text}%"
        query = query.filter(
            db.or_(
                Student.full_name.ilike(like),
                User.email.ilike(like),
                Student.branch.ilike(like),
            )
        )

    students = query.order_by(User.created_at.desc()).all()
    return jsonify([_format_student_row(student) for student in students]), 200


@admin_bp.route("/admin/student/<int:student_id>/blacklist", methods=["PUT"])
@admin_required
def blacklist_student(student_id):
    """Blacklist a student — blocks login and applying to drives."""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    if student.is_blacklisted:
        return jsonify({"message": "Student is already blacklisted"}), 400

    student.is_blacklisted = True
    db.session.commit()

    invalidate_admin_dashboard()
    invalidate_student_dashboard(student.user_id)

    return jsonify({"message": "Student blacklisted successfully"}), 200


@admin_bp.route("/admin/student/<int:student_id>/unblacklist", methods=["PUT"])
@admin_required
def unblacklist_student(student_id):
    """Remove a student from the blacklist (Activate)."""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    if not student.is_blacklisted:
        return jsonify({"message": "Student is not blacklisted"}), 400

    student.is_blacklisted = False
    db.session.commit()

    invalidate_admin_dashboard()
    invalidate_student_dashboard(student.user_id)

    return jsonify({"message": "Student activated successfully"}), 200


@admin_bp.route("/admin/profile", methods=["GET"])
@admin_required
def get_admin_profile():
    """
    GET /admin/profile

    Return the logged-in admin's profile details.
    """
    user_id = int(get_jwt_identity())
    admin = User.query.get(user_id)

    if not admin or admin.role != "admin":
        return jsonify({"message": "Admin not found"}), 404

    return jsonify({
        "name": admin.username,
        "email": admin.email,
        "role": admin.role,
        "created_at": admin.created_at.isoformat() if admin.created_at else None,
    }), 200


@admin_bp.route("/admin/profile", methods=["PUT"])
@admin_required
def update_admin_profile():
    """
    PUT /admin/profile

    Editable: name (username), password, email (optional).
    """
    user_id = int(get_jwt_identity())
    admin = User.query.get(user_id)

    if not admin or admin.role != "admin":
        return jsonify({"message": "Admin not found"}), 404

    data = request.get_json(silent=True) or {}

    name = data.get("name")
    if name is None or str(name).strip() == "":
        return jsonify({"message": "name is required"}), 400

    name = str(name).strip()
    if name != admin.username:
        existing = User.query.filter_by(username=name).first()
        if existing and existing.id != admin.id:
            return jsonify({"message": "Username already exists"}), 400
        admin.username = name

    email = data.get("email")
    if email is not None and str(email).strip() != "":
        email = str(email).strip()
        if email != admin.email:
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != admin.id:
                return jsonify({"message": "Email already exists"}), 400
            admin.email = email

    password = data.get("password")
    if password is not None and str(password).strip() != "":
        if len(str(password)) < 6:
            return jsonify({"message": "Password must be at least 6 characters"}), 400
        admin.set_password(str(password))

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully",
        "profile": {
            "name": admin.username,
            "email": admin.email,
            "role": admin.role,
            "created_at": admin.created_at.isoformat() if admin.created_at else None,
        },
    }), 200


@admin_bp.route("/admin/drives", methods=["GET"])
@admin_required
def get_all_drives():
    """
    Return all placement drives for admin review (Stage 7.1).

    Sorting: newest first (created_at DESC).
    Only accessible by admin users (JWT role = admin).
    """
    drives = (
        PlacementDrive.query.join(Company)
        .order_by(PlacementDrive.created_at.desc())
        .all()
    )

    return jsonify([_format_drive_row(drive) for drive in drives]), 200


@admin_bp.route("/admin/applications", methods=["GET"])
@admin_required
def get_all_applications():
    """
    Return every application for admin review.

    Query params (all optional):
      - search / q   free-text across student name, email, company, drive
      - status
      - company
      - student
      - drive

    Response fields:
      Application ID, Student Name, Student Email, Company, Drive,
      Applied Date, Status, Interview Date, Interview Mode, Final Result.
    """
    query = (
        Application.query
        .join(Student, Application.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
        .join(Company, PlacementDrive.company_id == Company.id)
    )

    status = (request.args.get("status") or "").strip()
    company = (request.args.get("company") or "").strip()
    student = (request.args.get("student") or "").strip()
    drive = (request.args.get("drive") or "").strip()
    free_text = (request.args.get("q") or request.args.get("search") or "").strip()

    if status:
        query = query.filter(Application.status == status)
    if company:
        query = query.filter(Company.company_name.ilike(f"%{company}%"))
    if student:
        query = query.filter(
            db.or_(
                Student.full_name.ilike(f"%{student}%"),
                User.email.ilike(f"%{student}%"),
            )
        )
    if drive:
        query = query.filter(PlacementDrive.job_title.ilike(f"%{drive}%"))
    if free_text:
        like = f"%{free_text}%"
        query = query.filter(
            db.or_(
                Student.full_name.ilike(like),
                User.email.ilike(like),
                Company.company_name.ilike(like),
                PlacementDrive.job_title.ilike(like),
                Application.status.ilike(like),
            )
        )

    applications = query.order_by(Application.application_date.desc()).all()
    return jsonify(
        [_format_application_admin_row(app) for app in applications]
    ), 200


def _validate_drive_action(drive, new_status):
    """
    Validation rules (Stage 7.1):
      - If already Approved → return message
      - If already Rejected → return message
    """
    if not drive:
        return jsonify({"message": "Placement drive not found"}), 404

    if drive.status == "Approved":
        return jsonify({"message": "Placement drive is already approved"}), 400

    if drive.status == "Rejected":
        return jsonify({"message": "Placement drive is already rejected"}), 400

    # Only allow the two admin actions in this stage
    if new_status not in ("Approved", "Rejected"):
        return jsonify({"message": "Invalid status update"}), 400

    return None, None


# Stage 7.1 drive approve/reject routes
def _company_user_id_for_drive(drive):
    """Return the owning company's user_id for cache invalidation."""
    if drive and drive.company:
        return drive.company.user_id
    return None


@admin_bp.route("/admin/drives/<int:drive_id>/approve", methods=["PUT"])
@admin_required
def approve_drive(drive_id):
    """
    Approve a placement drive (Stage 7.1).

    PUT /admin/drives/<id>/approve
    Updates: status = "Approved"
    """
    drive = PlacementDrive.query.get(drive_id)
    error_response, status_code = _validate_drive_action(drive, "Approved")
    if error_response:
        return error_response, status_code

    drive.status = "Approved"
    db.session.commit()

    # Stage 9.1: drive appears in student search / dashboards
    invalidate_after_drive_status_change(_company_user_id_for_drive(drive))

    return jsonify({"message": "Placement drive approved successfully"}), 200


@admin_bp.route("/admin/drives/<int:drive_id>/reject", methods=["PUT"])
@admin_required
def reject_drive(drive_id):
    """
    Reject a placement drive (Stage 7.1).

    PUT /admin/drives/<id>/reject
    Updates: status = "Rejected"
    """
    drive = PlacementDrive.query.get(drive_id)
    error_response, status_code = _validate_drive_action(drive, "Rejected")
    if error_response:
        return error_response, status_code

    drive.status = "Rejected"
    db.session.commit()

    invalidate_after_drive_status_change(_company_user_id_for_drive(drive))

    return jsonify({"message": "Placement drive rejected successfully"}), 200


# Backward-compatible Stage 4.2 routes (kept so older frontend code doesn't break)
@admin_bp.route("/admin/drive/<int:drive_id>/approve", methods=["PUT"])
@admin_required
def approve_drive_legacy(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    error_response, status_code = _validate_drive_action(drive, "Approved")
    if error_response:
        return error_response, status_code
    drive.status = "Approved"
    db.session.commit()
    invalidate_after_drive_status_change(_company_user_id_for_drive(drive))
    return jsonify({"message": "Placement drive approved successfully"}), 200


@admin_bp.route("/admin/drive/<int:drive_id>/reject", methods=["PUT"])
@admin_required
def reject_drive_legacy(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    error_response, status_code = _validate_drive_action(drive, "Rejected")
    if error_response:
        return error_response, status_code
    drive.status = "Rejected"
    db.session.commit()
    invalidate_after_drive_status_change(_company_user_id_for_drive(drive))
    return jsonify({"message": "Placement drive rejected successfully"}), 200


@admin_bp.route("/admin/test-reminder", methods=["POST"])
@admin_required
def test_reminder():
    """
    Stage 9.3: immediately queue the daily reminder Celery task.

    Admin only. Does not wait for emails to finish — returns task id/status.

    When Flask DEBUG=True, queues the task with bypass_date_window=True so
    demos can email for all upcoming eligible drives/interviews without the
    production reminder window. Scheduled Beat jobs never set this flag.
    """
    from flask import current_app

    from tasks import send_daily_reminders

    bypass_date_window = bool(current_app.debug)
    async_result = send_daily_reminders.delay(bypass_date_window=bypass_date_window)

    return jsonify({
        "task_id": async_result.id,
        "status": async_result.status,
        "bypass_date_window": bypass_date_window,
    }), 200


@admin_bp.route("/admin/test-monthly-report", methods=["POST"])
@admin_required
def test_monthly_report():
    """
    Stage 9.4: immediately queue the monthly placement report Celery task.

    Admin only. Returns task id/status without waiting for email to finish.
    """
    from tasks import generate_monthly_report

    async_result = generate_monthly_report.delay()

    return jsonify({
        "task_id": async_result.id,
        "status": async_result.status,
    }), 200
