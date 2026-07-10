"""
Application Model

Why this model exists:
When a student applies to a placement drive, we need to record that application
and track its status (Applied, Shortlisted, Interview, Selected, or Rejected).

Stage 8: interview fields store schedule details when a company shortlists
a student and moves them to the Interview stage.

Relationship:
- Each Application belongs to ONE Student (via student_id).
- Each Application belongs to ONE PlacementDrive (via drive_id).
- A Student can apply to many drives.
- A Drive can receive applications from many students.
"""

from datetime import datetime

from extensions import db


class Application(db.Model):
    """A student's application to a placement drive."""

    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign key links this application to the student who applied
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False,
    )

    # Foreign key links this application to the drive they applied for
    drive_id = db.Column(
        db.Integer,
        db.ForeignKey("placement_drives.id"),
        nullable=False,
    )

    application_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Status flow: Applied → Shortlisted → Interview → Selected / Rejected
    status = db.Column(db.String(20), default="Applied", nullable=False)

    # Optional notes from admin or company about this application
    remarks = db.Column(db.Text, nullable=True)

    # Interview schedule (Stage 8) — filled when company schedules an interview
    interview_date = db.Column(db.Date, nullable=True)
    interview_time = db.Column(db.String(10), nullable=True)   # e.g. "14:30"
    interview_mode = db.Column(db.String(20), nullable=True)    # Online / Offline

    def __repr__(self):
        return f"<Application student={self.student_id} drive={self.drive_id}>"
