"""
app.py - Main Flask Application Entry Point

This file creates and configures the Flask app.
Run this file to start the backend server:

    python app.py
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

    # Step 4: Register routes
    register_routes(app)

    return app


def register_routes(app):
    """Register all URL routes for the application."""

    @app.route("/", methods=["GET"])
    def home():
        """
        Test route to verify the backend is running.
        Visit http://localhost:5000/ in a browser or use curl.
        """
        return jsonify({"message": "Placement Portal Backend Running"})


# Create the app instance
app = create_app()


# Run the development server when this file is executed directly
if __name__ == "__main__":
    # debug=True enables auto-reload when code changes (development only)
    app.run(debug=True, host="0.0.0.0", port=5000)
