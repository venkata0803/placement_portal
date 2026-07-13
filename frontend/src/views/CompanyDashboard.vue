<script>
/**
 * CompanyDashboard.vue - Company Dashboard (Stage 5.1 + 9.5)
 *
 * Frontend flow:
 * 1. Router guard checks user is logged in with role "company"
 * 2. On mount, fetch dashboard + placement drives
 * 3. Stage 9.5: each drive has Export Applicants (Celery CSV)
 */

import {
  clearAuthData,
  downloadCompanyExport,
  getCompanyDashboard,
  getCompanyDrives,
  logout,
  requestCompanyExport,
  saveBlobDownload,
} from "../services/api.js";

export default {
  name: "CompanyDashboard",

  data() {
    return {
      loading: true,
      error: null,
      companyName: "",
      website: "",
      hrName: "",
      hrEmail: "",
      approvalStatus: "",
      totalPlacementDrives: 0,
      approvedDrives: 0,
      pendingDrives: 0,
      totalApplications: 0,
      // Stage 9.5: drives list for Export Applicants buttons
      drives: [],
      exportingDriveId: null,
      exportMessage: null,
      exportError: null,
    };
  },

  mounted() {
    this.fetchDashboardData();
  },

  methods: {
    /**
     * Fetch company dashboard summary and the company's placement drives.
     */
    async fetchDashboardData() {
      this.loading = true;
      this.error = null;

      try {
        const data = await getCompanyDashboard();

        this.companyName = data.company_name;
        this.website = data.website || "-";
        this.hrName = data.hr_name;
        this.hrEmail = data.hr_email;
        this.approvalStatus = data.approval_status;
        this.totalPlacementDrives = data.total_placement_drives;
        this.approvedDrives = data.approved_drives;
        this.pendingDrives = data.pending_drives;
        this.totalApplications = data.total_applications;

        // Load drives so each row can show Export Applicants
        try {
          this.drives = await getCompanyDrives();
        } catch (driveErr) {
          // Company may still be Pending — dashboard still shows without drives
          this.drives = [];
        }
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load dashboard data. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    /**
     * Poll until Celery finishes writing the CSV, then download it.
     */
    async waitAndDownloadCompanyCsv(filename) {
      const maxAttempts = 15;
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          const response = await downloadCompanyExport(filename);
          saveBlobDownload(response, filename);
          return true;
        } catch (err) {
          if (err.response?.status === 404 && attempt < maxAttempts) {
            await new Promise((resolve) => setTimeout(resolve, 1000));
            continue;
          }
          throw err;
        }
      }
      return false;
    },

    /**
     * Stage 9.5: Export Applicants for one placement drive.
     */
    async handleExportApplicants(drive) {
      this.exportingDriveId = drive.id;
      this.exportMessage = null;
      this.exportError = null;

      try {
        const data = await requestCompanyExport(drive.id);
        await this.waitAndDownloadCompanyCsv(data.filename);
        this.exportMessage = `Export ready for "${drive.title || drive.job_title}": ${data.filename}`;
      } catch (err) {
        this.exportError =
          err.response?.data?.message ||
          "Failed to export applicants. Is the Celery worker running?";
      } finally {
        this.exportingDriveId = null;
      }
    },

    /**
     * Log out the company user and redirect to the login page.
     */
    async handleLogout() {
      try {
        await logout();
      } catch (error) {
        console.error("Logout error:", error);
      }

      clearAuthData();
      this.$router.push("/login");
    },
  },
};
</script>

<template>
  <div class="company-dashboard">
    <!-- Top Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
      <span class="navbar-brand mb-0 h1">Company Dashboard</span>

      <div class="navbar-nav ms-auto flex-row align-items-center gap-2">
        <router-link class="nav-link text-light" to="/company">Dashboard</router-link>
        <router-link class="nav-link text-light" to="/company/drives">Placement Drives</router-link>
        <router-link class="nav-link text-light" to="/company/applicants">Applicants</router-link>
        <router-link class="nav-link text-light" to="/company/profile">Profile</router-link>
        <button
          type="button"
          class="btn btn-outline-light btn-sm ms-2"
          @click="handleLogout"
        >
          Logout
        </button>
      </div>
    </nav>

    <div class="d-flex company-layout">
      <!-- Sidebar -->
      <aside class="sidebar bg-light border-end p-3">
        <h6 class="text-muted text-uppercase small mb-3">Menu</h6>
        <ul class="nav flex-column">
          <li class="nav-item">
            <router-link class="nav-link active" to="/company">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/company/drives">Placement Drives</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/company/applicants">Applicants</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/company/profile">Profile</router-link>
          </li>
          <li class="nav-item mt-2">
            <button
              type="button"
              class="btn btn-outline-danger btn-sm w-100"
              @click="handleLogout"
            >
              Logout
            </button>
          </li>
        </ul>
      </aside>

      <!-- Main Content -->
      <main class="flex-grow-1 p-4">
        <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-2">
          <h2 class="mb-0">Overview</h2>
        </div>

        <div v-if="exportMessage" class="alert alert-success" role="alert">
          {{ exportMessage }}
        </div>
        <div v-if="exportError" class="alert alert-danger" role="alert">
          {{ exportError }}
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading dashboard...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>

        <!-- Dashboard Content -->
        <div v-else>
          <!-- Summary Cards -->
          <div class="row g-3 mb-4">
            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Total Drives</h6>
                  <p class="card-text display-6">{{ totalPlacementDrives }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Approved Drives</h6>
                  <p class="card-text display-6">{{ approvedDrives }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Pending Drives</h6>
                  <p class="card-text display-6">{{ pendingDrives }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Applications Received</h6>
                  <p class="card-text display-6">{{ totalApplications }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Company Information -->
          <div class="card shadow-sm mb-4">
            <div class="card-header">
              <h5 class="mb-0">Company Information</h5>
            </div>
            <div class="card-body">
              <dl class="row mb-0">
                <dt class="col-sm-3">Company Name</dt>
                <dd class="col-sm-9">{{ companyName }}</dd>

                <dt class="col-sm-3">Website</dt>
                <dd class="col-sm-9">{{ website }}</dd>

                <dt class="col-sm-3">HR Name</dt>
                <dd class="col-sm-9">{{ hrName }}</dd>

                <dt class="col-sm-3">HR Email</dt>
                <dd class="col-sm-9">{{ hrEmail }}</dd>

                <dt class="col-sm-3">Approval Status</dt>
                <dd class="col-sm-9">
                  <span
                    class="badge"
                    :class="{
                      'bg-success': approvalStatus === 'Approved',
                      'bg-warning text-dark': approvalStatus === 'Pending',
                      'bg-danger': approvalStatus === 'Rejected',
                      'bg-secondary': !approvalStatus,
                    }"
                  >
                    {{ approvalStatus }}
                  </span>
                </dd>
              </dl>
            </div>
          </div>

          <!-- Stage 9.5: Export Applicants per placement drive -->
          <div class="card shadow-sm">
            <div class="card-header">
              <h5 class="mb-0">Export Applicants</h5>
            </div>
            <div class="card-body p-0">
              <div class="table-responsive">
                <table class="table table-hover mb-0">
                  <thead class="table-light">
                    <tr>
                      <th>Drive Title</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="drives.length === 0">
                      <td colspan="3" class="text-center text-muted">
                        No placement drives available to export.
                      </td>
                    </tr>
                    <tr v-for="drive in drives" :key="drive.id">
                      <td>{{ drive.title || drive.job_title }}</td>
                      <td>{{ drive.status }}</td>
                      <td>
                        <button
                          type="button"
                          class="btn btn-sm btn-outline-primary"
                          :disabled="exportingDriveId !== null"
                          @click="handleExportApplicants(drive)"
                        >
                          <span
                            v-if="exportingDriveId === drive.id"
                            class="spinner-border spinner-border-sm me-1"
                            role="status"
                          ></span>
                          {{
                            exportingDriveId === drive.id
                              ? "Exporting..."
                              : "Export Applicants"
                          }}
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Match Student Dashboard shell: navbar, sidebar spacing, active + hover */
.company-layout {
  min-height: calc(100vh - 56px);
}

.sidebar {
  width: 220px;
  min-width: 220px;
  min-height: 100%;
  flex-shrink: 0;
}

.sidebar .nav-link {
  color: #212529;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.25rem;
  border-radius: 0.25rem;
}

.sidebar .nav-link:hover {
  color: #0d6efd;
  background-color: #f0f4f8;
}

.sidebar .nav-link.active {
  color: #0d6efd;
  background-color: #e7f1ff;
  font-weight: 600;
}

.navbar .nav-link.text-light {
  color: rgba(255, 255, 255, 0.9) !important;
}

.navbar .nav-link.text-light:hover {
  color: #ffffff !important;
  text-decoration: underline;
  text-underline-offset: 4px;
}

.navbar .nav-link.text-light.router-link-exact-active,
.navbar .nav-link.text-light.active {
  color: #ffffff !important;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 4px;
}

@media (max-width: 768px) {
  .company-layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    min-width: 100%;
    border-right: 0 !important;
    border-bottom: 1px solid #dee2e6;
  }
}
</style>
