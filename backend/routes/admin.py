"""
admin.py - Admin Dashboard Routes

Protected routes for admin users only.
Uses @admin_required decorator for JWT role validation.
"""

from flask import Blueprint, jsonify

from cache_helpers import (
    CACHE_TIMEOUT,
    admin_dashboard_key,
    invalidate_admin_dashboard,
    invalidate_after_drive_status_change,
    invalidate_company_dashboard,
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
        "approval_status": company.approval_status,
        "created_at": company.user.created_at.isoformat()
        if company.user.created_at
        else None,
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
    Return all companies for admin review.

    Fields: id, company_name, email, website, approval_status, created_at.
    Only accessible by admin users.
    """
    companies = (
        Company.query.join(User)
        .order_by(User.created_at.desc())
        .all()
    )

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
    """
    from tasks import send_daily_reminders

    async_result = send_daily_reminders.delay()

    return jsonify({
        "task_id": async_result.id,
        "status": async_result.status,
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
