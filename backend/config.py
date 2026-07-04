"""
config.py - Application Configuration

This file stores all settings for the Flask app.
We read values from environment variables (or .env file)
so secrets are not hard-coded in source code.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into os.environ
load_dotenv()


class Config:
    """Base configuration used by the Flask application."""

    # Secret key is used by Flask for sessions and security features
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # SQLite database connection string
    # sqlite:/// means the database file lives in the backend folder
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///placement_portal.db"
    )

    # Turn off modification tracking to save memory (recommended by Flask-SQLAlchemy)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT secret key for token signing (will be used when we add authentication)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")

    # Redis URL for Celery tasks (will be used later)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
