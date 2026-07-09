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

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from decorators import student_required
from extensions import db
from models import Application, PlacementDrive, Student

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


# ---------- Stage 6.1: Dashboard ----------


@student_bp.route("/student/dashboard", methods=["GET"])
@student_required
def get_dashboard():
    """
    GET /student/dashboard

    Returns student profile + overview counts for the Student Dashboard.
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

    return jsonify({
        "message": "Resume uploaded successfully",
        "resume_filename": unique_name,
    }), 200
