"""
app.py - Main Flask Application Entry Point

This file creates and configures the Flask app.
Run this file to start the backend server:

    python app.py

When the app starts:
1. All database tables are created automatically (db.create_all)
2. A default admin user is created if one does not already exist
"""

import os

from flask import Flask, jsonify
from config import Config
from extensions import db, migrate, cors, jwt, cache, mail


def create_app():
    """
    Application Factory Pattern

    Instead of creating the app globally, we use a function.
    This makes testing easier and keeps the code organized.
    """

    # Step 1: Create the Flask application instance
    app = Flask(__name__)

    # Step 2: Load configuration from config.py
    app.config.from_object(Config)

    # Step 3: Initialize all extensions with this app
    db.init_app(app)       # Connect SQLAlchemy to the app
    migrate.init_app(app, db)  # Connect Flask-Migrate to the app and database
    cors.init_app(app)     # Enable CORS for all routes
    jwt.init_app(app)      # Enable JWT support
    cache.init_app(app)    # Stage 9.1: Redis caching (see Config.CACHE_*)
    mail.init_app(app)     # Stage 9.3: email for daily reminders

    # Step 4: Create database tables, upload folder, and default admin user
    with app.app_context():
        # Import models so SQLAlchemy registers all table definitions
        import models  # noqa: F401

        # Create all tables in SQLite if they do not exist yet
        db.create_all()

        # SQLite create_all() does not add new columns to existing tables
        ensure_student_skills_column()
        ensure_student_blacklist_column()
        ensure_company_profile_columns()
        ensure_application_interview_columns()

        # Make sure resume upload and CSV export directories exist
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        os.makedirs(app.config["EXPORT_FOLDER"], exist_ok=True)

        # Create the default admin account on first run
        create_default_admin()

    # Step 5: Register blueprints (grouped API routes)
    from routes.auth import auth_bp
    from routes.test_routes import test_bp
    from routes.admin import admin_bp
    from routes.company import company_bp
    from routes.student import student_bp

    app.register_blueprint(auth_bp)
    if app.config.get("DEBUG"):
        app.register_blueprint(test_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    # Step 6: Register basic test routes
    register_routes(app)

    return app


def ensure_student_skills_column():
    """
    Stage 6.2: add students.skills if the database was created before this column existed.

    SQLite's create_all() only creates missing tables — it does not ALTER existing ones.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "students" not in inspector.get_table_names():
        return

    column_names = [col["name"] for col in inspector.get_columns("students")]
    if "skills" in column_names:
        return

    with db.engine.connect() as connection:
        connection.execute(text("ALTER TABLE students ADD COLUMN skills VARCHAR(500)"))
        connection.commit()
    print("Added students.skills column")


def ensure_student_blacklist_column():
    """Add students.is_blacklisted if the database predates this column."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "students" not in inspector.get_table_names():
        return

    column_names = [col["name"] for col in inspector.get_columns("students")]
    if "is_blacklisted" in column_names:
        return

    with db.engine.connect() as connection:
        connection.execute(
            text(
                "ALTER TABLE students ADD COLUMN is_blacklisted BOOLEAN "
                "NOT NULL DEFAULT 0"
            )
        )
        connection.commit()
    print("Added students.is_blacklisted column")


def ensure_company_profile_columns():
    """
    Add companies.industry and companies.location if missing.
    Also ensure companies.is_blacklisted exists on older databases.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "companies" not in inspector.get_table_names():
        return

    column_names = [col["name"] for col in inspector.get_columns("companies")]

    columns_to_add = [
        ("industry", "VARCHAR(100)"),
        ("location", "VARCHAR(100)"),
        ("is_blacklisted", "BOOLEAN NOT NULL DEFAULT 0"),
    ]

    with db.engine.connect() as connection:
        for column_name, column_type in columns_to_add:
            if column_name in column_names:
                continue
            connection.execute(
                text(f"ALTER TABLE companies ADD COLUMN {column_name} {column_type}")
            )
            print(f"Added companies.{column_name} column")
        connection.commit()


def ensure_application_interview_columns():
    """
    Stage 8: add interview columns to applications if the DB predates Stage 8.

    SQLite create_all() only creates missing tables — it does not ALTER existing ones.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "applications" not in inspector.get_table_names():
        return

    column_names = [col["name"] for col in inspector.get_columns("applications")]

    columns_to_add = [
        ("interview_date", "DATE"),
        ("interview_time", "VARCHAR(10)"),
        ("interview_mode", "VARCHAR(20)"),
    ]

    with db.engine.connect() as connection:
        for column_name, column_type in columns_to_add:
            if column_name in column_names:
                continue
            connection.execute(
                text(f"ALTER TABLE applications ADD COLUMN {column_name} {column_type}")
            )
            print(f"Added applications.{column_name} column")
        connection.commit()


def create_default_admin():
    """
    Automatic Admin Creation

    How it works:
    1. We search the database for a user with username "admin"
    2. If found -> print "Admin already exists" (do nothing)
    3. If not found -> create a new User with role "admin" and print success message

    This runs every time app.py starts, but the admin is only inserted once.
    """
    from models import User

    existing_admin = User.query.filter_by(username="admin").first()

    if existing_admin:
        # Fix old databases where admin password was stored as plain text
        if existing_admin.password == "admin123":
            existing_admin.set_password("admin123")
            db.session.commit()
        print("Admin already exists")
        return

    # Create the default admin user with a hashed password
    admin_user = User(
        username="admin",
        email="admin@placementportal.com",
        role="admin",
        is_active=True,
    )
    admin_user.set_password("admin123")

    db.session.add(admin_user)
    db.session.commit()
    print("Admin created successfully")


def register_routes(app):
    """Register all URL routes for the application."""
    from decorators import admin_required

    @app.route("/", methods=["GET"])
    def home():
        """
        Test route to verify the backend is running.
        Visit http://localhost:5000/ in a browser or use curl.
        """
        return jsonify({"message": "Placement Portal Backend Running"})

    @app.route("/test-celery", methods=["GET"])
    @admin_required
    def test_celery():
        """
        Stage 9.2: trigger the demo Celery task (admin only).

        Flow:
          1. hello_task.delay() sends the job to Redis (broker)
          2. The Celery worker picks it up and runs hello_task()
          3. The result is stored in Redis (backend)
          4. We return the task id and current status immediately
        """
        from tasks import hello_task

        async_result = hello_task.delay()

        return jsonify({
            "task_id": async_result.id,
            "status": async_result.status,
        }), 200

    if app.config.get("DEBUG"):

        @app.route("/tables", methods=["GET"])
        def table_counts():
            """
            Return the total number of rows in each database table.
            Useful to verify that models and tables were created correctly.
            """
            from models import User, Student, Company, PlacementDrive, Application

            return jsonify({
                "users": User.query.count(),
                "students": Student.query.count(),
                "companies": Company.query.count(),
                "placement_drives": PlacementDrive.query.count(),
                "applications": Application.query.count(),
            })

        @app.route("/admin-check", methods=["GET"])
        def admin_check():
            """
            Check whether the default admin user exists in the database.
            """
            from models import User

            admin_exists = User.query.filter_by(username="admin").first() is not None

            return jsonify({"admin_exists": admin_exists})


# Create the app instance
app = create_app()


# Run the development server when this file is executed directly
if __name__ == "__main__":
    # debug=True enables auto-reload when code changes (development only)
    app.run(debug=app.config.get("DEBUG", False), host="0.0.0.0", port=5000)
