"""
auth.py - Authentication Routes

Handles registration, login, logout, and current user info.

APIs:
- POST /register/student  - Create student account
- POST /register/company  - Create company account
- POST /login             - Login and get JWT token
- POST /logout            - Simple logout (client removes token)
- GET  /me                - Get logged-in user details
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from extensions import db
from models import Company, Student, User

# Blueprint groups all auth routes under one name
auth_bp = Blueprint("auth", __name__)


def _get_json_field(data, field_name):
    """Read a field from JSON body and strip extra spaces."""
    value = data.get(field_name)
    if isinstance(value, str):
        return value.strip()
    return value


def _validate_required_fields(data, required_fields):
    """
    Check that all required fields are present and not empty.
    Returns (is_valid, error_message).
    """
    for field_name in required_fields:
        value = _get_json_field(data, field_name)
        if value is None or value == "":
            return False, f"{field_name} is required"
    return True, None


def _check_duplicate_username(username):
    """Return error message if username already exists."""
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return "Username already exists"
    return None


def _check_duplicate_email(email):
    """Return error message if email already exists."""
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return "Email already exists"
    return None


@auth_bp.route("/register/student", methods=["POST"])
def register_student():
    """
    Register a new student.

    Creates:
    1. User row (role = "student", password is hashed)
    2. Student row (profile details)
    """
    data = request.get_json(silent=True) or {}

    # Step 1: Validate required fields
    required_fields = [
        "username",
        "email",
        "password",
        "full_name",
        "branch",
        "year",
        "cgpa",
        "phone",
    ]
    is_valid, error_message = _validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    # Step 2: Read and clean input values
    username = _get_json_field(data, "username")
    email = _get_json_field(data, "email")
    password = data.get("password")
    full_name = _get_json_field(data, "full_name")
    branch = _get_json_field(data, "branch")
    phone = _get_json_field(data, "phone")

    # Step 3: Check for duplicate username and email
    duplicate_error = _check_duplicate_username(username)
    if duplicate_error:
        return jsonify({"message": duplicate_error}), 400

    duplicate_error = _check_duplicate_email(email)
    if duplicate_error:
        return jsonify({"message": duplicate_error}), 400

    # Step 4: Convert numeric fields
    try:
        year = int(data.get("year"))
        cgpa = float(data.get("cgpa"))
    except (TypeError, ValueError):
        return jsonify({"message": "year and cgpa must be valid numbers"}), 400

    if cgpa < 0 or cgpa > 10:
        return jsonify({"message": "CGPA must be between 0 and 10"}), 400

    if year < 1 or year > 4:
        return jsonify({"message": "Year must be between 1 and 4"}), 400

    # Step 5: Create User with hashed password (never store plain text)
    new_user = User(
        username=username,
        email=email,
        role="student",
        is_active=True,
    )
    new_user.set_password(password)

    # Step 6: Create linked Student profile
    new_student = Student(
        user=new_user,
        full_name=full_name,
        branch=branch,
        year=year,
        cgpa=cgpa,
        phone=phone,
    )

    # Step 7: Save both rows to the database
    db.session.add(new_user)
    db.session.add(new_student)
    db.session.commit()

    return jsonify({"message": "Student registered successfully"}), 201


@auth_bp.route("/register/company", methods=["POST"])
def register_company():
    """
    Register a new company.

    Creates:
    1. User row (role = "company", password is hashed)
    2. Company row (approval_status defaults to "Pending")
    """
    data = request.get_json(silent=True) or {}

    # Step 1: Validate required fields
    required_fields = [
        "username",
        "email",
        "password",
        "company_name",
        "hr_name",
        "hr_email",
    ]
    is_valid, error_message = _validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    # Step 2: Read and clean input values
    username = _get_json_field(data, "username")
    email = _get_json_field(data, "email")
    password = data.get("password")
    company_name = _get_json_field(data, "company_name")
    hr_name = _get_json_field(data, "hr_name")
    hr_email = _get_json_field(data, "hr_email")
    website = _get_json_field(data, "website")
    description = _get_json_field(data, "description")

    # Step 3: Check for duplicate username and email
    duplicate_error = _check_duplicate_username(username)
    if duplicate_error:
        return jsonify({"message": duplicate_error}), 400

    duplicate_error = _check_duplicate_email(email)
    if duplicate_error:
        return jsonify({"message": duplicate_error}), 400

    # Step 4: Create User with hashed password
    new_user = User(
        username=username,
        email=email,
        role="company",
        is_active=True,
    )
    new_user.set_password(password)

    # Step 5: Create Company profile (approval_status = "Pending" by default)
    new_company = Company(
        user=new_user,
        company_name=company_name,
        website=website or None,
        hr_name=hr_name,
        hr_email=hr_email,
        description=description or None,
        approval_status="Pending",
    )

    # Step 6: Save to database
    db.session.add(new_user)
    db.session.add(new_company)
    db.session.commit()

    return jsonify({"message": "Company registered successfully"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login with email and password.

    Returns a JWT token if credentials are correct.
    """
    data = request.get_json(silent=True) or {}

    # Step 1: Validate required fields
    email = _get_json_field(data, "email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "email and password are required"}), 400

    # Step 2: Find user by email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    # Step 3: Verify password using Werkzeug hash check
    if not user.check_password(password):
        return jsonify({"message": "Invalid email or password"}), 401

    # Step 4: Check if account is active
    if not user.is_active:
        return jsonify({"message": "Account is disabled"}), 403

    # Step 4b: Company users must be approved before they can access the dashboard
    if user.role == "company":
        company = Company.query.filter_by(user_id=user.id).first()
        if company:
            if company.approval_status == "Rejected":
                return jsonify({"message": "Company registration rejected."}), 403
            if company.approval_status != "Approved":
                return jsonify({
                    "message": "Your company is waiting for admin approval."
                }), 403

    # Step 5: Create JWT token with user id and role inside it
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "username": user.username,
        },
    )

    # Step 6: Return token and basic user info to the frontend
    return jsonify({
        "token": access_token,
        "role": user.role,
        "username": user.username,
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Simple logout endpoint.

    Note: We do not use a token blacklist yet.
    The frontend removes the token from localStorage.
    """
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """
    Return details of the currently logged-in user.

    The JWT token must be sent in the Authorization header:
    Authorization: Bearer <token>
    """
    # Step 1: Read user id from the JWT token
    user_id = int(get_jwt_identity())

    # Step 2: Load user from database
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Step 3: Return basic profile info
    return jsonify({
        "username": user.username,
        "role": user.role,
        "email": user.email,
    }), 200
