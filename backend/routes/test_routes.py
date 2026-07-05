"""
test_routes.py - Role Protection Test Routes

These simple routes help verify that JWT role decorators work correctly.

Examples:
- GET /admin-test   -> only admin can access
- GET /student-test -> only student can access
- GET /company-test -> only company can access
"""

from flask import Blueprint, jsonify

from decorators import admin_required, company_required, student_required

test_bp = Blueprint("test", __name__)


@test_bp.route("/admin-test", methods=["GET"])
@admin_required
def admin_test():
    """Return success if the logged-in user is an admin."""
    return jsonify({"message": "Admin access granted"}), 200


@test_bp.route("/student-test", methods=["GET"])
@student_required
def student_test():
    """Return success if the logged-in user is a student."""
    return jsonify({"message": "Student access granted"}), 200


@test_bp.route("/company-test", methods=["GET"])
@company_required
def company_test():
    """Return success if the logged-in user is a company."""
    return jsonify({"message": "Company access granted"}), 200
