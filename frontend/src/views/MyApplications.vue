<script>
/**
 * MyApplications.vue (Stage 7 Combined)
 *
 * Shows the logged-in student's applications in a beginner-friendly table.
 * Data source: GET /student/applications
 */

import { clearAuthData, getMyApplications, logout } from "../services/api.js";

export default {
  name: "MyApplications",

  data() {
    return {
      loading: true,
      error: null,
      applications: [],
    };
  },

  mounted() {
    this.loadApplications();
  },

  methods: {
    async loadApplications() {
      this.loading = true;
      this.error = null;

      try {
        this.applications = await getMyApplications();
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load applications. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    formatDate(dateString) {
      if (!dateString) return "-";
      return new Date(dateString).toLocaleDateString();
    },

    statusBadgeClass(status) {
      if (status === "Selected") return "bg-success";
      if (status === "Rejected") return "bg-danger";
      if (status === "Interview") return "bg-orange";
      if (status === "Shortlisted") return "bg-warning text-dark";
      return "bg-primary";
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
  <div class="student-dashboard">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
      <span class="navbar-brand mb-0 h1">Student Dashboard</span>

      <div class="navbar-nav ms-auto flex-row align-items-center gap-2">
        <router-link class="nav-link text-light" to="/student">Dashboard</router-link>
        <router-link class="nav-link text-light" to="/student/drives">
          Browse Drives
        </router-link>
        <router-link class="nav-link text-light" to="/student/applications">
          My Applications
        </router-link>
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
      <aside class="sidebar bg-light border-end p-3">
        <h6 class="text-muted text-uppercase small mb-3">Menu</h6>
        <ul class="nav flex-column">
          <li class="nav-item">
            <router-link class="nav-link" to="/student">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/student/drives">Browse Drives</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link active" to="/student/applications">
              My Applications
            </router-link>
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

      <main class="flex-grow-1 p-4">
        <div class="d-flex align-items-center justify-content-between mb-3">
          <h2 class="mb-0">My Applications</h2>
          <button class="btn btn-outline-secondary btn-sm" @click="loadApplications">
            Refresh
          </button>
        </div>

        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading applications...</p>
        </div>

        <div v-else-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>

        <div v-else class="card shadow-sm">
          <div class="card-body p-0">
            <table class="table table-striped table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th scope="col">Job Title</th>
                  <th scope="col">Company</th>
                  <th scope="col">Applied Date</th>
                  <th scope="col">Current Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="applications.length === 0">
                  <td colspan="4" class="text-center text-muted py-4">
                    You have not applied to any drives yet.
                  </td>
                </tr>
                <tr v-for="app in applications" :key="app.id">
                  <td>{{ app.job_title }}</td>
                  <td>{{ app.company_name }}</td>
                  <td>{{ formatDate(app.applied_date) }}</td>
                  <td>
                    <span class="badge" :class="statusBadgeClass(app.status)">
                      {{ app.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
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

/* Bootstrap doesn't include an orange badge by default */
.bg-orange {
  background-color: #fd7e14;
}
</style>

