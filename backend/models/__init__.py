"""
models/ - Database Models

Import all models here so SQLAlchemy knows about every table
when we call db.create_all() in app.py.
"""

from models.user import User
from models.student import Student
from models.company import Company
from models.placement_drive import PlacementDrive
from models.application import Application

# List of all models - useful for reference during viva
__all__ = [
    "User",
    "Student",
    "Company",
    "PlacementDrive",
    "Application",
]
