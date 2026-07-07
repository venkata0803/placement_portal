"""
admin.py - Admin Dashboard Routes

Protected routes for admin users only.
Uses @admin_required decorator for JWT role validation.
"""

from flask import Blueprint, jsonify

from decorators import admin_required
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
