"""
User Model

Why this model exists:
Every person who uses the Placement Portal needs a login account.
This table stores their username, email, password, and role (admin / student / company).
Admin, students, and company HR users all share this same table.
"""

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model):
    """Login account for admin, student, or company users."""

    __tablename__ = "users"

    # Primary key - unique ID for each user
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    # Role can be: "admin", "student", or "company"
    role = db.Column(db.String(20), nullable=False)

    # is_active = False means the account is disabled
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship: One User can have ONE Student profile (if role is "student")
    # uselist=False means this is a one-to-one relationship, not one-to-many
    student_profile = db.relationship(
        "Student",
        backref="user",
        uselist=False,
    )

    # Relationship: One User can have ONE Company profile (if role is "company")
    company_profile = db.relationship(
        "Company",
        backref="user",
        uselist=False,
    )

    def set_password(self, plain_password):
        """
        Hash the password before saving to the database.
        Never store plain text passwords.
        """
        self.password = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        """
        Compare a plain text password with the stored hash.
        Returns True if they match, False otherwise.
        """
        return check_password_hash(self.password, plain_password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
