<script>
/**
 * PlacementDrives.vue - Company Placement Drives (Stage 5.2 + 5.3)
 *
 * Frontend flow:
 * 1. On mount, loadDrives() fetches GET /company/drives
 * 2. Create → Bootstrap modal → POST /company/drives → refresh table
 * 3. Edit → Bootstrap modal (pre-filled) → PUT /company/drives/<id> → refresh
 * 4. Close → confirmation dialog → PATCH /company/drives/<id>/close → refresh
 *
 * Badge colors:
 *   Pending  = yellow (warning)
 *   Approved = green  (success)
 *   Closed   = gray   (secondary)
 */

import {
  clearAuthData,
  closePlacementDrive,
  createPlacementDrive,
  getCompanyDrives,
  logout,
  updatePlacementDrive,
} from "../../services/api.js";

export default {
  name: "CompanyPlacementDrives",

  data() {
    return {
      loading: true,
      error: null,
      actionError: null,
      successMessage: null,
      drives: [],

      // Create modal state
      showCreateModal: false,

      // Edit modal state (Stage 5.3)
      showEditModal: false,
      editingDriveId: null,

      // Close confirmation dialog (Stage 5.3)
      showCloseModal: false,
      closingDriveId: null,
      closingDriveTitle: "",

      submitting: false,
      formError: null,

      // Shared form fields for create and edit
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

    // ---------- Create drive ----------

    openCreateModal() {
      this.clearDriveForm();
      this.formError = null;
      this.showCreateModal = true;
    },

    closeCreateModal() {
      this.showCreateModal = false;
      this.formError = null;
    },

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

    // ---------- Edit drive (Stage 5.3) ----------

    /**
     * Open Edit modal and populate form with the selected drive's values.
     * Closed drives cannot be edited (button is hidden; backend also blocks).
     */
    openEditModal(drive) {
      this.editingDriveId = drive.id;
      this.formError = null;

      // Populate form so the user sees current values
      this.driveForm = {
        job_title: drive.title || "",
        job_description: drive.job_description || "",
        eligible_branch: drive.eligible_branch || "",
        minimum_cgpa: drive.minimum_cgpa ?? "",
        eligible_year: drive.eligible_year ?? "",
        // datetime-local needs "YYYY-MM-DDTHH:MM" (no seconds / timezone)
        application_deadline: this.toDateTimeLocal(drive.deadline),
      };

      this.showEditModal = true;
    },

    closeEditModal() {
      this.showEditModal = false;
      this.editingDriveId = null;
      this.formError = null;
    },

    /**
     * Save edits via PUT /company/drives/<id>, then refresh the table.
     */
    async handleUpdateDrive() {
      this.submitting = true;
      this.formError = null;
      this.successMessage = null;
      this.actionError = null;

      try {
        const result = await updatePlacementDrive(
          this.editingDriveId,
          this.driveForm
        );
        this.successMessage =
          result.message || "Placement drive updated successfully.";
        this.closeEditModal();
        await this.loadDrives();
      } catch (err) {
        this.formError =
          err.response?.data?.message ||
          "Failed to update placement drive. Please try again.";
      } finally {
        this.submitting = false;
      }
    },

    // ---------- Close drive (Stage 5.3) ----------

    /**
     * Open Bootstrap confirmation dialog before closing a drive.
     */
    openCloseModal(drive) {
      this.closingDriveId = drive.id;
      this.closingDriveTitle = drive.title;
      this.showCloseModal = true;
    },

    closeCloseModal() {
      this.showCloseModal = false;
      this.closingDriveId = null;
      this.closingDriveTitle = "";
    },

    /**
     * Confirm close → PATCH /company/drives/<id>/close → refresh table.
     */
    async handleConfirmClose() {
      this.submitting = true;
      this.successMessage = null;
      this.actionError = null;

      try {
        const result = await closePlacementDrive(this.closingDriveId);
        this.successMessage =
          result.message || "Placement drive closed successfully.";
        this.closeCloseModal();
        await this.loadDrives();
      } catch (err) {
        // Keep the table visible — show action error above it
        this.actionError =
          err.response?.data?.message ||
          "Failed to close placement drive. Please try again.";
        this.closeCloseModal();
      } finally {
        this.submitting = false;
      }
    },

    // ---------- Helpers ----------

    /**
     * Convert ISO deadline to datetime-local input value.
     * Example: "2026-08-01T10:30:00" → "2026-08-01T10:30"
     */
    toDateTimeLocal(isoString) {
      if (!isoString) {
        return "";
      }

      // Take first 16 chars (YYYY-MM-DDTHH:MM) for datetime-local inputs
      return isoString.slice(0, 16);
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
     * Badge colors: Pending=yellow, Approved=green, Closed=gray.
     */
    getStatusBadgeClass(status) {
      if (status === "Pending") {
        return "bg-warning text-dark";
      }
      if (status === "Approved") {
        return "bg-success";
      }
      if (status === "Closed") {
        return "bg-secondary";
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
        <router-link class="nav-link text-light" to="/company/applicants">
          Applicants
        </router-link>
        <router-link class="nav-link text-light" to="/company/profile">
          Profile
        </router-link>
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

        <!-- Action Error (edit/close failures — does not hide the table) -->
        <div
          v-if="actionError"
          class="alert alert-danger alert-dismissible fade show"
          role="alert"
        >
          {{ actionError }}
          <button
            type="button"
            class="btn-close"
            @click="actionError = null"
          ></button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading placement drives...</p>
        </div>

        <!-- Load Error State (e.g. company approval pending) -->
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
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="drives.length === 0">
                  <td colspan="8" class="text-center text-muted">
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
                  <td>
                    <!-- Edit: hidden when Closed (backend also blocks) -->
                    <button
                      v-if="drive.status !== 'Closed'"
                      type="button"
                      class="btn btn-sm btn-outline-primary me-1"
                      @click="openEditModal(drive)"
                    >
                      Edit
                    </button>
                    <!-- Close: hidden when already Closed -->
                    <button
                      v-if="drive.status !== 'Closed'"
                      type="button"
                      class="btn btn-sm btn-outline-secondary"
                      @click="openCloseModal(drive)"
                    >
                      Close
                    </button>
                    <span v-if="drive.status === 'Closed'" class="text-muted small">
                      —
                    </span>
                  </td>
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
                  <select
                    id="eligibleYear"
                    v-model="driveForm.eligible_year"
                    class="form-select"
                    required
                  >
                    <option value="" disabled>Select year</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                  </select>
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

    <!-- Edit Drive Modal (Stage 5.3) -->
    <div
      v-if="showEditModal"
      class="modal fade show d-block"
      tabindex="-1"
      style="background-color: rgba(0, 0, 0, 0.5)"
      @click.self="closeEditModal"
    >
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Placement Drive</h5>
            <button
              type="button"
              class="btn-close"
              @click="closeEditModal"
            ></button>
          </div>

          <form @submit.prevent="handleUpdateDrive">
            <div class="modal-body">
              <div v-if="formError" class="alert alert-danger" role="alert">
                {{ formError }}
              </div>

              <div class="mb-3">
                <label for="editJobTitle" class="form-label">Job Title</label>
                <input
                  id="editJobTitle"
                  v-model="driveForm.job_title"
                  type="text"
                  class="form-control"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="editJobDescription" class="form-label">Description</label>
                <textarea
                  id="editJobDescription"
                  v-model="driveForm.job_description"
                  class="form-control"
                  rows="3"
                  required
                ></textarea>
              </div>

              <div class="mb-3">
                <label for="editEligibleBranch" class="form-label">
                  Eligible Branch
                </label>
                <input
                  id="editEligibleBranch"
                  v-model="driveForm.eligible_branch"
                  type="text"
                  class="form-control"
                  placeholder="e.g. CSE, ECE"
                  required
                />
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="editMinimumCgpa" class="form-label">
                    Minimum CGPA
                  </label>
                  <input
                    id="editMinimumCgpa"
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
                  <label for="editEligibleYear" class="form-label">
                    Eligible Year
                  </label>
                  <select
                    id="editEligibleYear"
                    v-model="driveForm.eligible_year"
                    class="form-select"
                    required
                  >
                    <option value="" disabled>Select year</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                  </select>
                </div>
              </div>

              <div class="mb-3">
                <label for="editApplicationDeadline" class="form-label">
                  Deadline
                </label>
                <input
                  id="editApplicationDeadline"
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
                @click="closeEditModal"
              >
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="submitting">
                <span
                  v-if="submitting"
                  class="spinner-border spinner-border-sm me-1"
                  role="status"
                ></span>
                Save
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Close Confirmation Dialog (Stage 5.3) -->
    <div
      v-if="showCloseModal"
      class="modal fade show d-block"
      tabindex="-1"
      style="background-color: rgba(0, 0, 0, 0.5)"
      @click.self="closeCloseModal"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Close Placement Drive</h5>
            <button
              type="button"
              class="btn-close"
              @click="closeCloseModal"
            ></button>
          </div>

          <div class="modal-body">
            <p class="mb-0">
              Are you sure you want to close
              <strong>{{ closingDriveTitle }}</strong>?
              Closed drives cannot be edited.
            </p>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="submitting"
              @click="closeCloseModal"
            >
              Cancel
            </button>
            <button
              type="button"
              class="btn btn-dark"
              :disabled="submitting"
              @click="handleConfirmClose"
            >
              <span
                v-if="submitting"
                class="spinner-border spinner-border-sm me-1"
                role="status"
              ></span>
              Confirm Close
            </button>
          </div>
        </div>
      </div>
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
