"""
cache_helpers.py - Stage 9.1 Redis Cache Keys and Invalidation

Beginner-friendly helpers so route files can:
  1. Build stable cache keys for @cache.cached
  2. Delete / bump related keys when data changes

Cached APIs (timeout 300s):
  - GET /admin/dashboard
  - GET /company/dashboard
  - GET /student/dashboard
  - GET /student/drives  (includes company / job / branch search)

NOT cached: login, register, apply, company/drive approval endpoints.
"""

from flask import request
from flask_jwt_extended import get_jwt_identity

from extensions import cache

# How long cached responses live (matches Config.CACHE_DEFAULT_TIMEOUT)
CACHE_TIMEOUT = 300

# Version counters — bumping clears every key that embeds that version
_STUDENT_DASH_VER = "ver:student_dashboard"
_STUDENT_DRIVES_VER = "ver:student_drives"
_COMPANY_DASH_VER = "ver:company_dashboard"


def _get_version(version_key):
    """Read a version counter from Redis (default 0)."""
    return cache.get(version_key) or 0


def _bump_version(version_key):
    """
    Increase a version counter so old keys stop matching.

    Easier than scanning Redis for every possible user/query key.
    """
    new_version = _get_version(version_key) + 1
    # timeout=0 means "keep forever" until we bump again
    cache.set(version_key, new_version, timeout=0)
    return new_version


# ---------- Cache key builders (used by @cache.cached key_prefix=...) ----------


def admin_dashboard_key():
    """Shared key — all admins see the same dashboard summary."""
    return "admin_dashboard"


def company_dashboard_key():
    """
    Per-company key (JWT identity = user id).

    Includes a global version so we can invalidate every company dashboard
    when needed, or a single company via delete_company_dashboard(user_id).
    """
    user_id = get_jwt_identity()
    ver = _get_version(_COMPANY_DASH_VER)
    return f"company_dashboard_{user_id}_v{ver}"


def student_dashboard_key():
    """Per-student key (JWT identity = user id) + global version."""
    user_id = get_jwt_identity()
    ver = _get_version(_STUDENT_DASH_VER)
    return f"student_dashboard_{user_id}_v{ver}"


def student_drives_key():
    """
    Per-student + search/filter query key.

    GET /student/drives is the portal's search endpoint
    (job_title, company_name, branch, year, minimum_cgpa).
    Results include already_applied, so the student id must be in the key.
    """
    user_id = get_jwt_identity()
    ver = _get_version(_STUDENT_DRIVES_VER)
    # Sort query args so ?a=1&b=2 and ?b=2&a=1 share one cache entry
    query_parts = sorted(request.args.items(multi=True))
    query_str = "&".join(f"{k}={v}" for k, v in query_parts)
    return f"student_drives_{user_id}_v{ver}_{query_str}"


# ---------- Invalidation helpers (call after successful DB commits) ----------


def invalidate_admin_dashboard():
    """Clear the shared admin dashboard cache."""
    cache.delete(admin_dashboard_key())


def invalidate_company_dashboard(user_id):
    """
    Clear one company's dashboard.

    user_id is the User.id linked to the Company (same as JWT identity).
    """
    ver = _get_version(_COMPANY_DASH_VER)
    cache.delete(f"company_dashboard_{user_id}_v{ver}")


def invalidate_all_company_dashboards():
    """Clear every company dashboard (bumps version)."""
    _bump_version(_COMPANY_DASH_VER)


def invalidate_student_dashboard(user_id):
    """Clear one student's dashboard."""
    ver = _get_version(_STUDENT_DASH_VER)
    cache.delete(f"student_dashboard_{user_id}_v{ver}")


def invalidate_all_student_dashboards():
    """
    Clear every student dashboard.

    Used when approved drive count changes (affects available_drives for all).
    """
    _bump_version(_STUDENT_DASH_VER)


def invalidate_student_drives():
    """
    Clear all cached drive search results for every student.

    Used when approved drives are created/updated/closed/approved/rejected.
    """
    _bump_version(_STUDENT_DRIVES_VER)


def invalidate_after_drive_status_change(company_user_id=None):
    """
    Drive approved / rejected / closed / edited while Approved.

    Affects admin counts, company counts, all students' available drives,
    and every student drive search result.
    """
    invalidate_admin_dashboard()
    if company_user_id is not None:
        invalidate_company_dashboard(company_user_id)
    else:
        invalidate_all_company_dashboards()
    invalidate_all_student_dashboards()
    invalidate_student_drives()
