<script>
/**
 * StudentDashboard.vue - Student Dashboard (Stage 6.1)
 *
 * Frontend Flow
 * -------------
 * 1. Router guard checks user is logged in with role "student"
 * 2. On mount, fetchDashboardData() calls GET /student/dashboard via Axios
 * 3. JWT token is attached automatically by the Axios interceptor in api.js
 * 4. Response data is stored in component state and shown in cards + info section
 *
 * Dashboard, Profile, and Logout are active.
 * Browse Drives and My Applications are disabled placeholders.
 */

import {
  clearAuthData,
  getStudentDashboard,
  logout,
} from "../services/api.js";

export default {
  name: "StudentDashboard",

  data() {
    return {
      loading: true,
      error: null,
      // Student profile fields
      fullName: "",
      email: "",
      branch: "",
      cgpa: "",
      year: "",
      resumeUploaded: "",
      // Overview card counts
      availableDrives: 0,
      appliedDrives: 0,
      selectedCount: 0,
      rejectedCount: 0,
    };
  },

  mounted() {
    this.fetchDashboardData();
  },

  methods: {
    /**
     * Fetch student dashboard data from the backend API.
     * Handles loading spinner and error messages.
     */
    async fetchDashboardData() {
      this.loading = true;
      this.error = null;

      try {
        const data = await getStudentDashboard();

        this.fullName = data.full_name;
        this.email = data.email;
        this.branch = data.branch;
        this.cgpa = data.cgpa;
        this.year = data.year;
        this.resumeUploaded = data.resume_uploaded;
        this.availableDrives = data.available_drives;
        this.appliedDrives = data.applied_drives;
        this.selectedCount = data.selected_count;
        this.rejectedCount = data.rejected_count;
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load dashboard data. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    /**
     * Log out the student and redirect to the login page.
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
  <div class="student-dashboard">
    <!-- Top Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
      <span class="navbar-brand mb-0 h1">Student Dashboard</span>

      <div class="navbar-nav ms-auto flex-row align-items-center gap-2">
        <router-link class="nav-link text-light" to="/student">Dashboard</router-link>
        <router-link class="nav-link text-light" to="/student/drives">
          Browse Drives
        </router-link>
        <span class="nav-link disabled text-secondary">My Applications</span>
        <router-link class="nav-link text-light" to="/student/profile">Profile</router-link>
        <button
          type="button"
          class="btn btn-outline-light btn-sm ms-2"
          @click="handleLogout"
        >
          Logout
        </button>
      </div>
    </nav>

    <div class="d-flex student-layout">
      <!-- Sidebar -->
      <aside class="sidebar bg-light border-end p-3">
        <h6 class="text-muted text-uppercase small mb-3">Menu</h6>
        <ul class="nav flex-column">
          <li class="nav-item">
            <router-link class="nav-link active" to="/student">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/student/drives">
              Browse Drives
            </router-link>
          </li>
          <li class="nav-item">
            <span class="nav-link disabled text-muted">My Applications</span>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/student/profile">Profile</router-link>
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
                  <h6 class="card-subtitle text-muted mb-2">Available Drives</h6>
                  <p class="card-text display-6">{{ availableDrives }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Applied Drives</h6>
                  <p class="card-text display-6">{{ appliedDrives }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Selected</h6>
                  <p class="card-text display-6">{{ selectedCount }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Rejected</h6>
                  <p class="card-text display-6">{{ rejectedCount }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Student Information -->
          <div class="card shadow-sm">
            <div class="card-header">
              <h5 class="mb-0">Student Information</h5>
            </div>
            <div class="card-body">
              <dl class="row mb-0">
                <dt class="col-sm-3">Name</dt>
                <dd class="col-sm-9">{{ fullName }}</dd>

                <dt class="col-sm-3">Email</dt>
                <dd class="col-sm-9">{{ email }}</dd>

                <dt class="col-sm-3">Branch</dt>
                <dd class="col-sm-9">{{ branch }}</dd>

                <dt class="col-sm-3">CGPA</dt>
                <dd class="col-sm-9">{{ cgpa }}</dd>

                <dt class="col-sm-3">Year</dt>
                <dd class="col-sm-9">{{ year }}</dd>

                <dt class="col-sm-3">Resume Status</dt>
                <dd class="col-sm-9">
                  <span
                    class="badge"
                    :class="{
                      'bg-success': resumeUploaded === 'Yes',
                      'bg-secondary': resumeUploaded !== 'Yes',
                    }"
                  >
                    {{ resumeUploaded }}
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
.student-layout {
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
