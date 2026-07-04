"""
Student Model

Why this model exists:
When a user registers as a "student", they need extra details like branch, CGPA,
and resume. This table stores that student-specific information.

Relationship:
- Each Student row links to exactly ONE User (via user_id).
- One User can have at most one Student profile.
"""

from extensions import db


class Student(db.Model):
    """Profile details for a student user."""

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign key links this student to their User account
    # unique=True ensures one User cannot have two Student profiles
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    full_name = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    resume_filename = db.Column(db.String(200), nullable=True)

    # Relationship: One Student can apply to MANY placement drives
    # Each application is stored in the Application table
    applications = db.relationship(
        "Application",
        backref="student",
        lazy=True,
    )

    def __repr__(self):
        return f"<Student {self.full_name}>"
