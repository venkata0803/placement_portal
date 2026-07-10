<script>
/**
 * AdminDashboard.vue - Admin Dashboard (Stage 4.1)
 *
 * Displays summary cards and recent student/company tables.
 * Fetches data from GET /admin/dashboard using Axios on mount.
 */

import { clearAuthData, getAdminDashboard, logout } from "../services/api.js";

export default {
  name: "AdminDashboard",

  data() {
    return {
      loading: true,
      error: null,
      totalStudents: 0,
      totalCompanies: 0,
      totalPlacementDrives: 0,
      totalApplications: 0,
      recentStudents: [],
      recentCompanies: [],
    };
  },

  mounted() {
    this.fetchDashboardData();
  },

  methods: {
    /**
     * Call the admin dashboard API and store the response in component data.
     */
    async fetchDashboardData() {
      this.loading = true;
      this.error = null;

      try {
        const data = await getAdminDashboard();

        this.totalStudents = data.total_students;
        this.totalCompanies = data.total_companies;
        this.totalPlacementDrives = data.total_placement_drives;
        this.totalApplications = data.total_applications;
        this.recentStudents = data.recent_students;
        this.recentCompanies = data.recent_companies;
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load dashboard data. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    /**
     * Format ISO date string for display in tables.
     */
    formatDate(dateString) {
      if (!dateString) {
        return "-";
      }

      const date = new Date(dateString);
      return date.toLocaleDateString();
    },

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
  <div class="admin-dashboard">
    <!-- Top Navbar -->
    <nav class="navbar navbar-dark bg-dark px-3">
      <span class="navbar-brand mb-0 h1">Admin Dashboard</span>
      <div class="ms-auto">
        <button
          type="button"
          class="btn btn-outline-light btn-sm"
          @click="handleLogout"
        >
          Logout
        </button>
      </div>
    </nav>

    <div class="d-flex admin-layout">
      <!-- Sidebar -->
      <aside class="sidebar bg-light border-end p-3">
        <h6 class="text-muted text-uppercase small mb-3">Menu</h6>
        <ul class="nav flex-column">
          <li class="nav-item">
            <router-link class="nav-link active" to="/admin">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/companies">Companies</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/drives">Placement Drives</router-link>
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
                  <h6 class="card-subtitle text-muted mb-2">Total Students</h6>
                  <p class="card-text display-6">{{ totalStudents }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Total Companies</h6>
                  <p class="card-text display-6">{{ totalCompanies }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Placement Drives</h6>
                  <p class="card-text display-6">{{ totalPlacementDrives }}</p>
                </div>
              </div>
            </div>

            <div class="col-sm-6 col-lg-3">
              <div class="card text-center shadow-sm">
                <div class="card-body">
                  <h6 class="card-subtitle text-muted mb-2">Applications</h6>
                  <p class="card-text display-6">{{ totalApplications }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Students Table -->
          <div class="card shadow-sm mb-4">
            <div class="card-header">
              <h5 class="mb-0">Recent Students</h5>
            </div>
            <div class="card-body p-0">
              <table class="table table-striped table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Email</th>
                    <th scope="col">Created Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="recentStudents.length === 0">
                    <td colspan="3" class="text-center text-muted">
                      No students registered yet.
                    </td>
                  </tr>
                  <tr
                    v-for="(student, index) in recentStudents"
                    :key="'student-' + index"
                  >
                    <td>{{ student.name }}</td>
                    <td>{{ student.email }}</td>
                    <td>{{ formatDate(student.created_at) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Recent Companies Table -->
          <div class="card shadow-sm">
            <div class="card-header">
              <h5 class="mb-0">Recent Companies</h5>
            </div>
            <div class="card-body p-0">
              <table class="table table-striped table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Email</th>
                    <th scope="col">Created Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="recentCompanies.length === 0">
                    <td colspan="3" class="text-center text-muted">
                      No companies registered yet.
                    </td>
                  </tr>
                  <tr
                    v-for="(company, index) in recentCompanies"
                    :key="'company-' + index"
                  >
                    <td>{{ company.name }}</td>
                    <td>{{ company.email }}</td>
                    <td>{{ formatDate(company.created_at) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
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
