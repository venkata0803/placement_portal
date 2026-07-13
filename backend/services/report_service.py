"""
report_service.py - Monthly Placement Activity Report (Stage 9.4)

This file only builds report data and HTML.
The Celery task in tasks.py calls these functions, then emails the admin.

Statistics cover the CURRENT calendar month only (not lifetime totals).

Required metrics (MAD-II):
  - Number of drives conducted this month
  - Number of students applied this month
  - Number of students selected this month
"""

from datetime import datetime

from models import Application, Company, PlacementDrive, Student, User


def _current_month_range(now):
    """
    Return [start, end) datetime bounds for the current UTC calendar month.
    """
    start = datetime(now.year, now.month, 1)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)
    return start, end


def collect_report_statistics():
    """
    Count the numbers shown on the monthly report for the CURRENT month only.

    Uses simple SQLAlchemy .count() queries so the logic is easy to explain.
    """
    now = datetime.utcnow()
    month_start, month_end = _current_month_range(now)

    # Students / companies registered this month
    total_students = (
        Student.query.join(User)
        .filter(User.created_at >= month_start, User.created_at < month_end)
        .count()
    )
    total_companies = (
        Company.query.join(User)
        .filter(User.created_at >= month_start, User.created_at < month_end)
        .count()
    )
    # Companies that became Approved and were registered this month
    approved_companies = (
        Company.query.join(User)
        .filter(
            Company.approval_status == "Approved",
            User.created_at >= month_start,
            User.created_at < month_end,
        )
        .count()
    )

    # Drives conducted this month = drives created this month
    # (Approved / Closed / Pending / Rejected all counted by created_at)
    drives_conducted = PlacementDrive.query.filter(
        PlacementDrive.created_at >= month_start,
        PlacementDrive.created_at < month_end,
    ).count()
    approved_drives = PlacementDrive.query.filter(
        PlacementDrive.status == "Approved",
        PlacementDrive.created_at >= month_start,
        PlacementDrive.created_at < month_end,
    ).count()
    pending_drives = PlacementDrive.query.filter(
        PlacementDrive.status == "Pending",
        PlacementDrive.created_at >= month_start,
        PlacementDrive.created_at < month_end,
    ).count()

    # Students applied this month (applications submitted in current month)
    students_applied = Application.query.filter(
        Application.application_date >= month_start,
        Application.application_date < month_end,
    ).count()
    shortlisted_students = Application.query.filter(
        Application.status == "Shortlisted",
        Application.application_date >= month_start,
        Application.application_date < month_end,
    ).count()
    # Students selected this month (Selected status, applied in current month)
    students_selected = Application.query.filter(
        Application.status == "Selected",
        Application.application_date >= month_start,
        Application.application_date < month_end,
    ).count()
    rejected_students = Application.query.filter(
        Application.status == "Rejected",
        Application.application_date >= month_start,
        Application.application_date < month_end,
    ).count()

    # Total Placements = students Selected this month
    total_placements = students_selected

    return {
        "current_month": now.strftime("%B %Y"),
        "generation_date": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        # Required MAD-II monthly metrics
        "drives_conducted": drives_conducted,
        "students_applied": students_applied,
        "students_selected": students_selected,
        # Extra supporting metrics
        "total_students": total_students,
        "total_companies": total_companies,
        "approved_companies": approved_companies,
        "total_placement_drives": drives_conducted,
        "approved_drives": approved_drives,
        "pending_drives": pending_drives,
        "total_applications": students_applied,
        "shortlisted_students": shortlisted_students,
        "selected_students": students_selected,
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

    Leads with the three required current-month metrics.
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
      <div class="col-md-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Drives Conducted This Month</div>
            <div class="fs-4 fw-semibold">{stats["drives_conducted"]}</div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Students Applied This Month</div>
            <div class="fs-4 fw-semibold">{stats["students_applied"]}</div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Students Selected This Month</div>
            <div class="fs-4 fw-semibold">{stats["students_selected"]}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Students Registered</div>
            <div class="fs-4 fw-semibold">{stats["total_students"]}</div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-body">
            <div class="text-muted small">Companies Registered</div>
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
        <strong>Placement Statistics (Current Month Only)</strong>
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
              <td>Drives Conducted This Month</td>
              <td>{stats["drives_conducted"]}</td>
            </tr>
            <tr>
              <td>Students Applied This Month</td>
              <td>{stats["students_applied"]}</td>
            </tr>
            <tr>
              <td>Students Selected This Month</td>
              <td>{stats["students_selected"]}</td>
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
              <td>Shortlisted Students</td>
              <td>{stats["shortlisted_students"]}</td>
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
      All counts are for the current calendar month only.
    </p>
  </div>
</body>
</html>
"""
