<script>
/**
 * AdminApplications.vue - Admin View All Applications
 *
 * Lists every application via GET /admin/applications.
 * Supports search and filters: Status, Company, Student, Drive.
 */

import {
  clearAuthData,
  fetchAdminApplications,
  logout,
} from "../services/api.js";

export default {
  name: "AdminApplications",

  data() {
    return {
      loading: true,
      error: null,
      applications: [],
      filters: {
        search: "",
        status: "",
        company: "",
        student: "",
        drive: "",
      },
      statusOptions: [
        "Applied",
        "Shortlisted",
        "Interview",
        "Selected",
        "Rejected",
      ],
    };
  },

  mounted() {
    this.loadApplications();
  },

  methods: {
    buildParams() {
      const params = {};
      if (this.filters.search.trim()) {
        params.search = this.filters.search.trim();
      }
      if (this.filters.status) {
        params.status = this.filters.status;
      }
      if (this.filters.company.trim()) {
        params.company = this.filters.company.trim();
      }
      if (this.filters.student.trim()) {
        params.student = this.filters.student.trim();
      }
      if (this.filters.drive.trim()) {
        params.drive = this.filters.drive.trim();
      }
      return params;
    },

    async loadApplications() {
      this.loading = true;
      this.error = null;

      try {
        this.applications = await fetchAdminApplications(this.buildParams());
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load applications. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    handleSearch() {
      this.loadApplications();
    },

    clearFilters() {
      this.filters = {
        search: "",
        status: "",
        company: "",
        student: "",
        drive: "",
      };
      this.loadApplications();
    },

    formatDate(dateString) {
      if (!dateString) {
        return "-";
      }
      return new Date(dateString).toLocaleDateString();
    },

    statusBadgeClass(status) {
      if (status === "Selected") return "bg-success";
      if (status === "Rejected") return "bg-danger";
      if (status === "Interview") return "bg-orange";
      if (status === "Shortlisted") return "bg-warning text-dark";
      return "bg-primary";
    },

    finalResultBadgeClass(result) {
      if (result === "Selected") return "bg-success";
      if (result === "Rejected") return "bg-danger";
      return "bg-secondary";
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
      <aside class="sidebar bg-light border-end p-3">
        <h6 class="text-muted text-uppercase small mb-3">Menu</h6>
        <ul class="nav flex-column">
          <li class="nav-item">
            <router-link class="nav-link" to="/admin">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/students">Students</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/companies">Companies</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/drives">
              Placement Drives
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link active" to="/admin/applications">
              Applications
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/profile">Profile</router-link>
          </li>
        </ul>
      </aside>

      <main class="flex-grow-1 p-4">
        <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-2">
          <h2 class="mb-0">Applications</h2>
          <button
            type="button"
            class="btn btn-outline-secondary btn-sm"
            :disabled="loading"
            @click="loadApplications"
          >
            Refresh
          </button>
        </div>

        <div class="card shadow-sm mb-4">
          <div class="card-body">
            <form class="row g-3" @submit.prevent="handleSearch">
              <div class="col-md-4">
                <label class="form-label">Search</label>
                <input
                  v-model="filters.search"
                  type="text"
                  class="form-control"
                  placeholder="Student, email, company, drive..."
                />
              </div>
              <div class="col-md-2">
                <label class="form-label">Status</label>
                <select v-model="filters.status" class="form-select">
                  <option value="">All</option>
                  <option
                    v-for="status in statusOptions"
                    :key="status"
                    :value="status"
                  >
                    {{ status }}
                  </option>
                </select>
              </div>
              <div class="col-md-2">
                <label class="form-label">Company</label>
                <input
                  v-model="filters.company"
                  type="text"
                  class="form-control"
                  placeholder="Company name"
                />
              </div>
              <div class="col-md-2">
                <label class="form-label">Student</label>
                <input
                  v-model="filters.student"
                  type="text"
                  class="form-control"
                  placeholder="Name or email"
                />
              </div>
              <div class="col-md-2">
                <label class="form-label">Drive</label>
                <input
                  v-model="filters.drive"
                  type="text"
                  class="form-control"
                  placeholder="Drive title"
                />
              </div>
              <div class="col-12 d-flex gap-2">
                <button type="submit" class="btn btn-primary" :disabled="loading">
                  Search
                </button>
                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  :disabled="loading"
                  @click="clearFilters"
                >
                  Clear
                </button>
              </div>
            </form>
          </div>
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
            <div class="table-responsive">
              <table class="table table-striped table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th scope="col">Application ID</th>
                    <th scope="col">Student Name</th>
                    <th scope="col">Student Email</th>
                    <th scope="col">Company</th>
                    <th scope="col">Drive</th>
                    <th scope="col">Applied Date</th>
                    <th scope="col">Status</th>
                    <th scope="col">Interview Date</th>
                    <th scope="col">Interview Mode</th>
                    <th scope="col">Final Result</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="applications.length === 0">
                    <td colspan="10" class="text-center text-muted py-4">
                      No applications found.
                    </td>
                  </tr>
                  <tr v-for="app in applications" :key="app.id">
                    <td>{{ app.id }}</td>
                    <td>{{ app.student_name }}</td>
                    <td>{{ app.student_email }}</td>
                    <td>{{ app.company }}</td>
                    <td>{{ app.drive }}</td>
                    <td>{{ formatDate(app.applied_date) }}</td>
                    <td>
                      <span class="badge" :class="statusBadgeClass(app.status)">
                        {{ app.status }}
                      </span>
                    </td>
                    <td>{{ formatDate(app.interview_date) }}</td>
                    <td>{{ app.interview_mode || "-" }}</td>
                    <td>
                      <span
                        class="badge"
                        :class="finalResultBadgeClass(app.final_result)"
                      >
                        {{ app.final_result }}
                      </span>
                    </td>
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

.bg-orange {
  background-color: #fd7e14;
}
</style>
