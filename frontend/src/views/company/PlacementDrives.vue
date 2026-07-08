<script>
/**
 * PlacementDrives.vue - Company Placement Drives (Stage 5.2)
 *
 * Frontend flow:
 * 1. On mount, loadDrives() fetches GET /company/drives
 * 2. User clicks "Create New Drive" → Bootstrap modal opens
 * 3. User fills form and submits → POST /company/drives
 * 4. On success: clear form, close modal, show alert, refresh table
 */

import {
  clearAuthData,
  createPlacementDrive,
  getCompanyDrives,
  logout,
} from "../../services/api.js";

export default {
  name: "CompanyPlacementDrives",

  data() {
    return {
      loading: true,
      error: null,
      successMessage: null,
      drives: [],
      showCreateModal: false,
      submitting: false,
      formError: null,
      driveForm: {
        job_title: "",
        job_description: "",
        eligible_branch: "",
        minimum_cgpa: "",
        eligible_year: "",
        application_deadline: "",
      },
    };
  },

  mounted() {
    this.loadDrives();
  },

  methods: {
    /**
     * Fetch placement drives for the logged-in company.
     */
    async loadDrives() {
      this.loading = true;
      this.error = null;

      try {
        this.drives = await getCompanyDrives();
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load placement drives. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    /**
     * Open the create drive modal and reset form errors.
     */
    openCreateModal() {
      this.formError = null;
      this.showCreateModal = true;
    },

    /**
     * Close the create drive modal.
     */
    closeCreateModal() {
      this.showCreateModal = false;
      this.formError = null;
    },

    /**
     * Reset the create drive form to empty values.
     */
    clearDriveForm() {
      this.driveForm = {
        job_title: "",
        job_description: "",
        eligible_branch: "",
        minimum_cgpa: "",
        eligible_year: "",
        application_deadline: "",
      };
    },

    /**
     * Submit the create drive form to POST /company/drives.
     */
    async handleCreateDrive() {
      this.submitting = true;
      this.formError = null;
      this.successMessage = null;

      try {
        await createPlacementDrive(this.driveForm);

        this.successMessage = "Placement drive created successfully.";
        this.clearDriveForm();
        this.closeCreateModal();
        await this.loadDrives();
      } catch (err) {
        this.formError =
          err.response?.data?.message ||
          "Failed to create placement drive. Please try again.";
      } finally {
        this.submitting = false;
      }
    },

    /**
     * Format ISO date string for table display.
     */
    formatDate(dateString) {
      if (!dateString) {
        return "-";
      }

      const date = new Date(dateString);
      return date.toLocaleDateString();
    },

    /**
     * Return Bootstrap badge class based on drive status.
     */
    getStatusBadgeClass(status) {
      if (status === "Pending") {
        return "bg-warning text-dark";
      }
      if (status === "Approved") {
        return "bg-success";
      }
      if (status === "Rejected") {
        return "bg-danger";
      }
      return "bg-secondary";
    },

    /**
     * Log out the company user and redirect to login.
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
  <div class="company-drives">
    <!-- Top Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
      <span class="navbar-brand mb-0 h1">Company Dashboard</span>

      <div class="navbar-nav ms-auto flex-row align-items-center gap-2">
        <router-link class="nav-link text-light" to="/company">Dashboard</router-link>
        <router-link class="nav-link text-light active" to="/company/drives">
          Placement Drives
        </router-link>
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
            <router-link class="nav-link" to="/company">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link active" to="/company/drives">
              Placement Drives
            </router-link>
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
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="mb-0">Placement Drives</h2>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="loading || !!error"
            @click="openCreateModal"
          >
            Create New Drive
          </button>
        </div>

        <!-- Success Alert -->
        <div
          v-if="successMessage"
          class="alert alert-success alert-dismissible fade show"
          role="alert"
        >
          {{ successMessage }}
          <button
            type="button"
            class="btn-close"
            @click="successMessage = null"
          ></button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading placement drives...</p>
        </div>

        <!-- Error State (e.g. company approval pending) -->
        <div v-else-if="error" class="alert alert-warning" role="alert">
          {{ error }}
        </div>

        <!-- Drives Table -->
        <div v-else class="card shadow-sm">
          <div class="card-body p-0">
            <table class="table table-striped table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">Eligible Branch</th>
                  <th scope="col">CGPA</th>
                  <th scope="col">Year</th>
                  <th scope="col">Deadline</th>
                  <th scope="col">Status</th>
                  <th scope="col">Created Date</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="drives.length === 0">
                  <td colspan="7" class="text-center text-muted">
                    No placement drives created yet.
                  </td>
                </tr>
                <tr v-for="drive in drives" :key="drive.id">
                  <td>{{ drive.title }}</td>
                  <td>{{ drive.eligible_branch }}</td>
                  <td>{{ drive.minimum_cgpa }}</td>
                  <td>{{ drive.eligible_year }}</td>
                  <td>{{ formatDate(drive.deadline) }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadgeClass(drive.status)">
                      {{ drive.status }}
                    </span>
                  </td>
                  <td>{{ formatDate(drive.created_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>

    <!-- Create Drive Modal -->
    <div
      v-if="showCreateModal"
      class="modal fade show d-block"
      tabindex="-1"
      style="background-color: rgba(0, 0, 0, 0.5)"
      @click.self="closeCreateModal"
    >
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Create New Placement Drive</h5>
            <button
              type="button"
              class="btn-close"
              @click="closeCreateModal"
            ></button>
          </div>

          <form @submit.prevent="handleCreateDrive">
            <div class="modal-body">
              <div v-if="formError" class="alert alert-danger" role="alert">
                {{ formError }}
              </div>

              <div class="mb-3">
                <label for="jobTitle" class="form-label">Job Title</label>
                <input
                  id="jobTitle"
                  v-model="driveForm.job_title"
                  type="text"
                  class="form-control"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="jobDescription" class="form-label">Description</label>
                <textarea
                  id="jobDescription"
                  v-model="driveForm.job_description"
                  class="form-control"
                  rows="3"
                  required
                ></textarea>
              </div>

              <div class="mb-3">
                <label for="eligibleBranch" class="form-label">Eligible Branch</label>
                <input
                  id="eligibleBranch"
                  v-model="driveForm.eligible_branch"
                  type="text"
                  class="form-control"
                  placeholder="e.g. CSE, ECE"
                  required
                />
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="minimumCgpa" class="form-label">Minimum CGPA</label>
                  <input
                    id="minimumCgpa"
                    v-model="driveForm.minimum_cgpa"
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    class="form-control"
                    required
                  />
                </div>

                <div class="col-md-6 mb-3">
                  <label for="eligibleYear" class="form-label">Eligible Year</label>
                  <input
                    id="eligibleYear"
                    v-model="driveForm.eligible_year"
                    type="number"
                    min="1"
                    max="5"
                    class="form-control"
                    required
                  />
                </div>
              </div>

              <div class="mb-3">
                <label for="applicationDeadline" class="form-label">Deadline</label>
                <input
                  id="applicationDeadline"
                  v-model="driveForm.application_deadline"
                  type="datetime-local"
                  class="form-control"
                  required
                />
              </div>
            </div>

            <div class="modal-footer">
              <button
                type="button"
                class="btn btn-secondary"
                :disabled="submitting"
                @click="closeCreateModal"
              >
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="submitting">
                <span
                  v-if="submitting"
                  class="spinner-border spinner-border-sm me-1"
                  role="status"
                ></span>
                Submit
              </button>
            </div>
          </form>
        </div>
      </div>
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
