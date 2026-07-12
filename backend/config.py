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

    # Debug mode — gates development-only routes (/tables, /admin-check, test routes)
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

    # SQLite database connection string
    # sqlite:/// means the database file lives in the backend folder
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///placement_portal.db"
    )

    # Turn off modification tracking to save memory (recommended by Flask-SQLAlchemy)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT secret key for token signing (will be used when we add authentication)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")

    # Redis URL — Flask-Caching (Stage 9.1) and Celery broker/backend (Stage 9.2)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Stage 9.1: Flask-Caching with Redis (timeout = 300 seconds)
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # Stage 9.2: Celery uses the same Redis URL as broker and result backend
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Stage 9.3: Celery Beat schedule mode
    # false -> run daily reminders at 9:00 AM (Asia/Kolkata)
    # true  -> run every 1 minute (easy local testing)
    CELERY_BEAT_TEST_MODE = os.getenv(
        "CELERY_BEAT_TEST_MODE", "false"
    ).lower() in ("1", "true", "yes")

    # Stage 9.3: Flask-Mail settings (Gmail app password works well for demos)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        MAIL_USERNAME or "noreply@placementportal.com",
    )
    # true = do not contact SMTP (useful when testing without real credentials)
    MAIL_SUPPRESS_SEND = os.getenv("MAIL_SUPPRESS_SEND", "false").lower() in (
        "1",
        "true",
        "yes",
    )

    # Stage 6.2: resume uploads (PDF only, max 5 MB)
    # Files are stored under backend/uploads/resumes/
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB — Flask rejects larger requests

    # Stage 9.5: async CSV exports
    EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")
