<script>
/**
 * Students.vue - Admin Student Management
 *
 * Lists all registered students.
 * Admin can Blacklist or Activate each student after confirmation.
 * UI updates immediately after a successful action.
 */

import {
  clearAuthData,
  fetchStudents,
  blacklistStudent,
  unblacklistStudent,
  logout,
} from "../services/api.js";

export default {
  name: "Students",

  data() {
    return {
      loading: true,
      error: null,
      students: [],
      actionLoading: false,
      filters: {
        name: "",
        email: "",
        branch: "",
        year: "",
      },
    };
  },

  mounted() {
    this.loadStudents();
  },

  methods: {
    buildParams() {
      const params = {};
      if (this.filters.name.trim()) params.name = this.filters.name.trim();
      if (this.filters.email.trim()) params.email = this.filters.email.trim();
      if (this.filters.branch.trim()) params.branch = this.filters.branch.trim();
      if (this.filters.year.trim()) params.year = this.filters.year.trim();
      return params;
    },

    async loadStudents() {
      this.loading = true;
      this.error = null;

      try {
        this.students = await fetchStudents(this.buildParams());
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load students. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    handleSearch() {
      this.loadStudents();
    },

    clearFilters() {
      this.filters = {
        name: "",
        email: "",
        branch: "",
        year: "",
      };
      this.loadStudents();
    },

    async handleBlacklist(student) {
      const confirmed = window.confirm(
        `Blacklist student "${student.full_name}"? They will not be able to login or apply for drives.`
      );
      if (!confirmed) {
        return;
      }

      this.actionLoading = true;

      try {
        await blacklistStudent(student.id);
        student.is_blacklisted = true;
      } catch (err) {
        alert(
          err.response?.data?.message ||
            "Failed to blacklist student. Please try again."
        );
      } finally {
        this.actionLoading = false;
      }
    },

    async handleActivate(student) {
      const confirmed = window.confirm(
        `Activate student "${student.full_name}"?`
      );
      if (!confirmed) {
        return;
      }

      this.actionLoading = true;

      try {
        await unblacklistStudent(student.id);
        student.is_blacklisted = false;
      } catch (err) {
        alert(
          err.response?.data?.message ||
            "Failed to activate student. Please try again."
        );
      } finally {
        this.actionLoading = false;
      }
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
            <router-link class="nav-link active" to="/admin/students">
              Students
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/companies">
              Companies
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/drives">
              Placement Drives
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/applications">
              Applications
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/profile">Profile</router-link>
          </li>
        </ul>
      </aside>

      <main class="flex-grow-1 p-4">
        <h2 class="mb-4">Student Management</h2>

        <div class="card shadow-sm mb-4">
          <div class="card-body">
            <form class="row g-3" @submit.prevent="handleSearch">
              <div class="col-md-3">
                <label class="form-label">Name</label>
                <input
                  v-model="filters.name"
                  type="text"
                  class="form-control"
                  placeholder="Student name"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">Email</label>
                <input
                  v-model="filters.email"
                  type="text"
                  class="form-control"
                  placeholder="Email"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">Branch</label>
                <input
                  v-model="filters.branch"
                  type="text"
                  class="form-control"
                  placeholder="Branch"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">Year</label>
                <select v-model="filters.year" class="form-select">
                  <option value="">All</option>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4</option>
                </select>
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
          <p class="mt-2 text-muted">Loading students...</p>
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
                    <th scope="col">Name</th>
                    <th scope="col">Email</th>
                    <th scope="col">Branch</th>
                    <th scope="col">Year</th>
                    <th scope="col">CGPA</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="students.length === 0">
                    <td colspan="7" class="text-center text-muted">
                      No students registered yet.
                    </td>
                  </tr>
                  <tr v-for="student in students" :key="student.id">
                    <td>{{ student.full_name }}</td>
                    <td>{{ student.email }}</td>
                    <td>{{ student.branch }}</td>
                    <td>{{ student.year }}</td>
                    <td>{{ student.cgpa }}</td>
                    <td>
                      <span
                        v-if="student.is_blacklisted"
                        class="badge bg-danger"
                      >
                        Blacklisted
                      </span>
                      <span v-else class="badge bg-success">Active</span>
                    </td>
                    <td>
                      <button
                        v-if="!student.is_blacklisted"
                        class="btn btn-sm btn-warning"
                        :disabled="actionLoading"
                        @click="handleBlacklist(student)"
                      >
                        Blacklist
                      </button>
                      <button
                        v-else
                        class="btn btn-sm btn-success"
                        :disabled="actionLoading"
                        @click="handleActivate(student)"
                      >
                        Activate
                      </button>
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
</style>
