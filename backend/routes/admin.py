"""
admin.py - Admin Dashboard Routes

Protected routes for admin users only.
Uses @admin_required decorator for JWT role validation.
"""

from flask import Blueprint, jsonify

from decorators import admin_required
from extensions import db
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
def get_dashboard():
    """
    Admin Dashboard API.

    Returns summary counts and recent student/company registrations.
    Only accessible by users with role "admin" in their JWT token.
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
    """Build one placement drive entry for the admin drives list."""
    return {
        "id": drive.id,
        "drive_title": drive.job_title,
        "company": drive.company.company_name,
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

    return jsonify({"message": "Company rejected successfully"}), 200


@admin_bp.route("/admin/drives", methods=["GET"])
@admin_required
def get_all_drives():
    """
    Return all placement drives for admin review.

    Fields: drive_title, company, status, deadline, created_at.
    Only accessible by admin users.
    """
    drives = (
        PlacementDrive.query.join(Company)
        .order_by(PlacementDrive.created_at.desc())
        .all()
    )

    return jsonify([_format_drive_row(drive) for drive in drives]), 200


@admin_bp.route("/admin/drive/<int:drive_id>/approve", methods=["PUT"])
@admin_required
def approve_drive(drive_id):
    """Set placement drive status to Approved."""
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"message": "Placement drive not found"}), 404

    drive.status = "Approved"
    db.session.commit()

    return jsonify({"message": "Placement drive approved successfully"}), 200


@admin_bp.route("/admin/drive/<int:drive_id>/reject", methods=["PUT"])
@admin_required
def reject_drive(drive_id):
    """Set placement drive status to Rejected."""
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"message": "Placement drive not found"}), 404

    drive.status = "Rejected"
    db.session.commit()

    return jsonify({"message": "Placement drive rejected successfully"}), 200
