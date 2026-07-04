"""
app.py - Main Flask Application Entry Point

This file creates and configures the Flask app.
Run this file to start the backend server:

    python app.py

When the app starts:
1. All database tables are created automatically (db.create_all)
2. A default admin user is created if one does not already exist
"""

from flask import Flask, jsonify
from config import Config
from extensions import db, migrate, cors, jwt


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

    # Step 4: Create database tables and default admin user
    with app.app_context():
        # Import models so SQLAlchemy registers all table definitions
        import models  # noqa: F401

        # Create all tables in SQLite if they do not exist yet
        db.create_all()

        # Create the default admin account on first run
        create_default_admin()

    # Step 5: Register routes
    register_routes(app)

    return app


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
        print("Admin already exists")
        return

    # Create the default admin user
    admin_user = User(
        username="admin",
        email="admin@placementportal.com",
        password="admin123",
        role="admin",
        is_active=True,
    )

    db.session.add(admin_user)
    db.session.commit()
    print("Admin created successfully")


def register_routes(app):
    """Register all URL routes for the application."""

    @app.route("/", methods=["GET"])
    def home():
        """
        Test route to verify the backend is running.
        Visit http://localhost:5000/ in a browser or use curl.
        """
        return jsonify({"message": "Placement Portal Backend Running"})

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
    app.run(debug=True, host="0.0.0.0", port=5000)
