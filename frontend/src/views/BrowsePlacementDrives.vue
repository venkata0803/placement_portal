<script>
/**
 * BrowsePlacementDrives.vue (Stage 7.2)
 *
 * Frontend flow:
 * - Student selects search/filter inputs
 * - We call getApprovedDrives({ ...queryParams }) which hits GET /student/drives
 * - Backend returns ONLY status="Approved" drives (no apply action in this stage)
 * - Student can open "View Details" modal to read the full description + eligibility
 */

import {
  applyToDrive,
  clearAuthData,
  getApprovedDrives,
  logout,
} from "../services/api.js";

export default {
  name: "BrowsePlacementDrives",

  data() {
    return {
      loading: true,
      error: null,
      drives: [],
      successMessage: null,

      // Search / filter fields (sent as query params)
      jobTitle: "",
      companyName: "",
      branch: "",
      year: "",
      minimumCgpa: "",

      // Modal state (simple beginner-friendly modal, no Bootstrap JS needed)
      showModal: false,
      selectedDrive: null,
    };
  },

  mounted() {
    this.loadDrives();
  },

  methods: {
    /**
     * Build query params and fetch drives from GET /student/drives.
     *
     * Search flow:
     * - job_title and company_name use "contains" matching on the backend
     *
     * Filter flow:
     * - branch uses contains matching (because backend stores branches as text)
     * - year is exact match
     * - minimum_cgpa keeps drives whose minimum requirement <= provided CGPA
     */
    async loadDrives() {
      this.loading = true;
      this.error = null;
      this.successMessage = null;

      const params = {
        job_title: this.jobTitle || undefined,
        company_name: this.companyName || undefined,
        branch: this.branch || undefined,
        year: this.year || undefined,
        minimum_cgpa: this.minimumCgpa || undefined,
      };

      try {
        this.drives = await getApprovedDrives(params);
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load approved placement drives. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    clearFilters() {
      this.jobTitle = "";
      this.companyName = "";
      this.branch = "";
      this.year = "";
      this.minimumCgpa = "";
      this.loadDrives();
    },

    openDetails(drive) {
      this.selectedDrive = drive;
      this.showModal = true;
    },

    closeDetails() {
      this.showModal = false;
      this.selectedDrive = null;
    },

    async handleApply(drive) {
      // Frontend UX check (backend still enforces all rules)
      if (!drive || drive.already_applied) {
        return;
      }

      const confirmed = window.confirm(
        `Apply for "${drive.job_title}" at ${drive.company_name}?`
      );
      if (!confirmed) return;

      this.successMessage = null;
      this.error = null;

      try {
        const res = await applyToDrive(drive.id);
        this.successMessage = res?.message || "Applied successfully.";
        await this.loadDrives(); // refresh so Apply becomes disabled
      } catch (err) {
        this.error =
          err.response?.data?.message || "Failed to apply. Please try again.";
      }
    },

    formatDate(dateString) {
      if (!dateString) return "-";
      return new Date(dateString).toLocaleDateString();
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
          Placement History
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
            <router-link class="nav-link active" to="/student/drives">
              Browse Drives
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/student/applications">
              Placement History
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
          <h2 class="mb-0">Browse Approved Placement Drives</h2>
          <button class="btn btn-outline-secondary btn-sm" @click="loadDrives">
            Refresh
          </button>
        </div>

        <div v-if="successMessage" class="alert alert-success" role="alert">
          {{ successMessage }}
        </div>

        <!-- Search + filters -->
        <div class="card shadow-sm mb-3">
          <div class="card-body">
            <div class="row g-2 align-items-end">
              <div class="col-md-3">
                <label class="form-label">Job Title</label>
                <input
                  v-model="jobTitle"
                  type="text"
                  class="form-control"
                  placeholder="e.g. Software Engineer"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">Company</label>
                <input
                  v-model="companyName"
                  type="text"
                  class="form-control"
                  placeholder="e.g. Google"
                />
              </div>
              <div class="col-md-2">
                <label class="form-label">Branch</label>
                <select v-model="branch" class="form-select">
                  <option value="">All</option>
                  <option value="CSE">CSE</option>
                  <option value="ECE">ECE</option>
                  <option value="EEE">EEE</option>
                  <option value="MECH">MECH</option>
                  <option value="CIVIL">CIVIL</option>
                </select>
              </div>
              <div class="col-md-2">
                <label class="form-label">Year</label>
                <select v-model="year" class="form-select">
                  <option value="">All</option>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4</option>
                </select>
              </div>
              <div class="col-md-2">
                <label class="form-label">Your CGPA</label>
                <input
                  v-model="minimumCgpa"
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  class="form-control"
                  placeholder="e.g. 7.5"
                />
              </div>

              <div class="col-12 d-flex gap-2 mt-2">
                <button class="btn btn-primary" @click="loadDrives">Search</button>
                <button class="btn btn-outline-secondary" @click="clearFilters">
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading / error -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading approved placement drives...</p>
        </div>

        <div v-else-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>

        <!-- Results -->
        <div v-else class="card shadow-sm">
          <div class="card-body p-0">
            <table class="table table-striped table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th scope="col">Job Title</th>
                  <th scope="col">Company</th>
                  <th scope="col">Branch</th>
                  <th scope="col">Min CGPA</th>
                  <th scope="col">Year</th>
                  <th scope="col">Deadline</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="drives.length === 0">
                  <td colspan="7" class="text-center text-muted py-4">
                    No approved placement drives found for your search/filters.
                  </td>
                </tr>
                <tr v-for="drive in drives" :key="drive.id">
                  <td>{{ drive.job_title }}</td>
                  <td>{{ drive.company_name }}</td>
                  <td>{{ drive.eligible_branch }}</td>
                  <td>{{ drive.minimum_cgpa }}</td>
                  <td>{{ drive.eligible_year }}</td>
                  <td>{{ formatDate(drive.deadline) }}</td>
                  <td>
                    <button
                      class="btn btn-sm btn-outline-primary me-2"
                      @click="openDetails(drive)"
                    >
                      View Details
                    </button>
                    <button
                      class="btn btn-sm"
                      :class="drive.already_applied ? 'btn-secondary' : 'btn-success'"
                      :disabled="!!drive.already_applied"
                      @click="handleApply(drive)"
                    >
                      {{ drive.already_applied ? "Already Applied" : "Apply" }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Redesigned modal (Bootstrap layout, controlled by Vue state) -->
        <div
          v-if="showModal"
          class="modal-backdrop-custom"
          @click.self="closeDetails"
        >
          <div class="modal-dialog modal-dialog-centered modal-lg w-100">
            <div class="modal-content">
              <div class="modal-header">
                <div>
                  <h5 class="modal-title mb-0">
                    {{ selectedDrive?.job_title || "Drive Details" }}
                  </h5>
                  <div class="text-muted small">
                    {{ selectedDrive?.company_name || "-" }}
                  </div>
                </div>
                <button type="button" class="btn-close" @click="closeDetails" />
              </div>

              <div class="modal-body">
                <div class="row g-3">
                  <div class="col-12">
                    <div class="card">
                      <div class="card-body">
                        <div class="fw-semibold mb-1">Description</div>
                        <div class="text-muted">
                          {{ selectedDrive?.description || "-" }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="col-md-6">
                    <div class="card h-100">
                      <div class="card-body">
                        <div class="fw-semibold mb-2">Eligibility</div>
                        <div class="row g-2">
                          <div class="col-12">
                            <div class="d-flex justify-content-between">
                              <span class="text-muted">Eligible Branch</span>
                              <span class="fw-semibold">
                                {{ selectedDrive?.eligible_branch || "-" }}
                              </span>
                            </div>
                          </div>
                          <div class="col-12">
                            <div class="d-flex justify-content-between">
                              <span class="text-muted">Minimum CGPA</span>
                              <span class="fw-semibold">
                                {{ selectedDrive?.minimum_cgpa ?? "-" }}
                              </span>
                            </div>
                          </div>
                          <div class="col-12">
                            <div class="d-flex justify-content-between">
                              <span class="text-muted">Eligible Year</span>
                              <span class="fw-semibold">
                                {{ selectedDrive?.eligible_year ?? "-" }}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="col-md-6">
                    <div class="card h-100">
                      <div class="card-body">
                        <div class="fw-semibold mb-2">Timeline</div>
                        <div class="d-flex justify-content-between mb-2">
                          <span class="text-muted">Deadline</span>
                          <span class="fw-semibold">
                            {{ formatDate(selectedDrive?.deadline) }}
                          </span>
                        </div>
                        <div class="d-flex justify-content-between">
                          <span class="text-muted">Status</span>
                          <span class="fw-semibold">
                            {{ selectedDrive?.status || "Approved" }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="modal-footer">
                <button class="btn btn-secondary" @click="closeDetails">
                  Close
                </button>
                <button
                  class="btn"
                  :class="selectedDrive?.already_applied ? 'btn-secondary' : 'btn-success'"
                  :disabled="!!selectedDrive?.already_applied"
                  @click="handleApply(selectedDrive)"
                >
                  {{ selectedDrive?.already_applied ? "Already Applied" : "Apply" }}
                </button>
              </div>
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

.modal-backdrop-custom {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 1050;
}

.modal-dialog {
  max-width: 900px;
}
</style>

