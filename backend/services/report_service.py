"""
report_service.py - Monthly Placement Activity Report (Stage 9.4)

This file only builds report data and HTML.
The Celery task in tasks.py calls these functions, then emails the admin.
"""

from datetime import datetime

from models import Application, Company, PlacementDrive, Student, User


def collect_report_statistics():
    """
    Count the numbers shown on the monthly report.

    Uses simple SQLAlchemy .count() queries so the logic is easy to explain.
    """
    now = datetime.utcnow()

    total_students = Student.query.count()
    total_companies = Company.query.count()
    approved_companies = Company.query.filter_by(approval_status="Approved").count()

    total_drives = PlacementDrive.query.count()
    approved_drives = PlacementDrive.query.filter_by(status="Approved").count()
    pending_drives = PlacementDrive.query.filter_by(status="Pending").count()

    total_applications = Application.query.count()
    shortlisted_students = Application.query.filter_by(status="Shortlisted").count()
    selected_students = Application.query.filter_by(status="Selected").count()
    rejected_students = Application.query.filter_by(status="Rejected").count()

    # Total Placements = students who got Selected (same count used for viva clarity)
    total_placements = selected_students

    return {
        "current_month": now.strftime("%B %Y"),
        "generation_date": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_students": total_students,
        "total_companies": total_companies,
        "approved_companies": approved_companies,
        "total_placement_drives": total_drives,
        "approved_drives": approved_drives,
        "pending_drives": pending_drives,
        "total_applications": total_applications,
        "shortlisted_students": shortlisted_students,
        "selected_students": selected_students,
        "rejected_students": rejected_students,
        "total_placements": total_placements,
    }


def get_admin_email():
    """
    Find the admin user's email address.

    Sends the monthly report only to this admin account.
    """
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        return None
    return admin.email


def build_monthly_report_html(stats):
    """
    Build one Bootstrap HTML page for the monthly report.

    Uses a CDN Bootstrap stylesheet, simple cards, and one summary table.
    No PDF — HTML only (as required for Stage 9.4).
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Monthly Placement Report</title>
  <link
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
    rel="stylesheet"
  >
</head>
<body class="bg-light">
  <div class="container py-4">
    <div class="mb-4">
      <h1 class="h3 mb-1">Institute Placement Portal</h1>
      <p class="text-muted mb-0">Monthly Placement Activity Report</p>
      <p class="mb-0"><strong>Current Month:</strong> {stats["current_month"]}</p>
      <p><strong>Generation Date:</strong> {stats["generation_date"]}</p>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Total Students</div>
            <div class="fs-4 fw-semibold">{stats["total_students"]}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Total Companies</div>
            <div class="fs-4 fw-semibold">{stats["total_companies"]}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Approved Companies</div>
            <div class="fs-4 fw-semibold">{stats["approved_companies"]}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Total Placements</div>
            <div class="fs-4 fw-semibold">{stats["total_placements"]}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card border-0 shadow-sm">
      <div class="card-header bg-white">
        <strong>Placement Statistics</strong>
      </div>
      <div class="card-body p-0">
        <table class="table table-striped table-hover mb-0">
          <thead class="table-light">
            <tr>
              <th scope="col">Metric</th>
              <th scope="col">Count</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Total Placement Drives</td>
              <td>{stats["total_placement_drives"]}</td>
            </tr>
            <tr>
              <td>Approved Drives</td>
              <td>{stats["approved_drives"]}</td>
            </tr>
            <tr>
              <td>Pending Drives</td>
              <td>{stats["pending_drives"]}</td>
            </tr>
            <tr>
              <td>Total Applications</td>
              <td>{stats["total_applications"]}</td>
            </tr>
            <tr>
              <td>Shortlisted Students</td>
              <td>{stats["shortlisted_students"]}</td>
            </tr>
            <tr>
              <td>Selected Students</td>
              <td>{stats["selected_students"]}</td>
            </tr>
            <tr>
              <td>Rejected Students</td>
              <td>{stats["rejected_students"]}</td>
            </tr>
            <tr>
              <td>Total Placements</td>
              <td>{stats["total_placements"]}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p class="text-muted small mt-4 mb-0">
      This report was generated automatically by the Placement Portal Celery job.
    </p>
  </div>
</body>
</html>
"""
