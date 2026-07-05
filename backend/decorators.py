"""
decorators.py - Role-Based Route Protection

These decorators protect routes so only users with the correct role can access them.

How it works:
1. @jwt_required() checks that a valid JWT token was sent in the request header
2. We read the "role" claim from the token
3. If the role matches, the route runs; otherwise we return 403 Unauthorized
"""

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required


def _role_required(required_role):
    """
    Helper that creates a role-checking decorator.

    required_role: "admin", "student", or "company"
    """

    def decorator(view_function):
        @wraps(view_function)
        @jwt_required()
        def wrapper(*args, **kwargs):
            # Step 1: Read extra data stored inside the JWT token
            token_data = get_jwt()
            user_role = token_data.get("role")

            # Step 2: Compare token role with the role required for this route
            if user_role != required_role:
                return jsonify({"message": "Unauthorized - wrong role"}), 403

            # Step 3: Role matches, so run the actual route function
            return view_function(*args, **kwargs)

        return wrapper

    return decorator


# Simple decorators for each role (easy to use in routes)
admin_required = _role_required("admin")
student_required = _role_required("student")
company_required = _role_required("company")
