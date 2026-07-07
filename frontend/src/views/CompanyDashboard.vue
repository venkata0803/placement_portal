<script>
/**
 * CompanyDashboard.vue - Company Dashboard (Stage 5.1)
 *
 * Frontend flow:
 * 1. Router guard checks user is logged in with role "company"
 * 2. On mount, fetchDashboardData() calls GET /company/dashboard via Axios
 * 3. JWT token is attached automatically by the Axios interceptor in api.js
 * 4. Response data is stored in component state and shown in cards + info section
 */

import {
  clearAuthData,
  getCompanyDashboard,
  logout,
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
    };
  },

  mounted() {
    this.fetchDashboardData();
  },

  methods: {
    /**
     * Fetch company dashboard data from the backend API.
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
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load dashboard data. Please try again.";
      } finally {
        this.loading = false;
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
        <span class="nav-link disabled text-secondary">Placement Drives</span>
        <span class="nav-link disabled text-secondary">Applicants</span>
        <span class="nav-link disabled text-secondary">Profile</span>
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
            <span class="nav-link disabled text-muted">Placement Drives</span>
          </li>
          <li class="nav-item">
            <span class="nav-link disabled text-muted">Applicants</span>
          </li>
          <li class="nav-item">
            <span class="nav-link disabled text-muted">Profile</span>
          </li>
        </ul>
      </aside>

      <!-- Main Content -->
      <main class="flex-grow-1 p-4">
        <h2 class="mb-4">Overview</h2>

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
          <div class="card shadow-sm">
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
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.company-layout {
  min-height: calc(100vh - 56px);
}

.sidebar {
  width: 220px;
  min-height: 100%;
}

.nav-link.active {
  color: #0d6efd;
  background-color: #e7f1ff;
  border-radius: 0.25rem;
}
</style>
