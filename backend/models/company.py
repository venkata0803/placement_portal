"""
Company Model

Why this model exists:
When a user registers as a "company", they need company-specific details like
company name, HR contact, and approval status. This table stores that information.

Relationship:
- Each Company row links to exactly ONE User (via user_id).
- One User can have at most one Company profile.
- One Company can create MANY Placement Drives.
"""

from extensions import db


class Company(db.Model):
    """Profile details for a company user."""

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign key links this company to their User account
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    company_name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    hr_name = db.Column(db.String(100), nullable=False)
    hr_email = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # approval_status can be: "Pending", "Approved", or "Rejected"
    # Admin must approve a company before they can post drives
    approval_status = db.Column(db.String(20), default="Pending", nullable=False)

    # Blacklisted companies cannot login or create drives
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)

    # Relationship: One Company can create MANY Placement Drives
    placement_drives = db.relationship(
        "PlacementDrive",
        backref="company",
        lazy=True,
    )

    def __repr__(self):
        return f"<Company {self.company_name}>"
