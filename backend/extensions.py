"""
extensions.py - Flask Extensions

We create extension objects here WITHOUT attaching them to the app yet.
This avoids circular import problems and works well with the app factory pattern.

Each extension is initialized in app.py using init_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Database ORM - used to define models and run queries
db = SQLAlchemy()

# Database migrations - used to update database schema safely
migrate = Migrate()

# Cross-Origin Resource Sharing - allows frontend (Vue) to call backend APIs
cors = CORS()

# JSON Web Token manager - used for login/authentication (later)
jwt = JWTManager()
