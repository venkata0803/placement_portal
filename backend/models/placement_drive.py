"""
PlacementDrive Model

Why this model exists:
Companies post job openings (placement drives) for students to apply.
This table stores details about each drive such as job title, eligibility, and deadline.

Relationship:
- Each drive belongs to ONE Company (via company_id).
- One Company can create MANY drives.
- One Drive can receive MANY Applications from students.
"""

from datetime import datetime

from extensions import db


class PlacementDrive(db.Model):
    """A job placement drive posted by a company."""

    __tablename__ = "placement_drives"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign key links this drive to the company that created it
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
    )

    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)

    # Which branch(es) can apply - stored as text, e.g. "CSE, ECE"
    eligible_branch = db.Column(db.String(100), nullable=False)

    minimum_cgpa = db.Column(db.Float, nullable=False)

    # Which year of study can apply, e.g. 3 for third year
    eligible_year = db.Column(db.Integer, nullable=False)

    application_deadline = db.Column(db.DateTime, nullable=False)

    # status can be: "Pending", "Approved", "Rejected", or "Closed"
    status = db.Column(db.String(20), default="Pending", nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship: One Drive can have MANY Applications from students
    applications = db.relationship(
        "Application",
        backref="drive",
        lazy=True,
    )

    def __repr__(self):
        return f"<PlacementDrive {self.job_title}>"
