"""
company.py - Company Dashboard Routes

Protected routes for company users only.
Uses @company_required decorator for JWT role validation.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

from decorators import company_required
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
