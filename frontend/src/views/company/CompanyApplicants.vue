<script>
/**
 * CompanyApplicants.vue (Stage 8)
 *
 * Frontend flow:
 * 1. Load company's placement drives (GET /company/drives)
 * 2. Click "View Applicants" on a drive
 * 3. Load applicants for that drive (GET /company/drives/<id>/applications)
 * 4. Actions: View Profile, update status, schedule interview
 *
 * Status badges:
 *   Applied     = blue   (primary)
 *   Shortlisted = yellow (warning)
 *   Interview   = orange
 *   Selected    = green  (success)
 *   Rejected    = red    (danger)
 */

import {
  clearAuthData,
  getCompanyDrives,
  getDriveApplications,
  logout,
  scheduleApplicationInterview,
  updateApplicationStatus,
} from "../../services/api.js";

export default {
  name: "CompanyApplicants",

  data() {
    return {
      loadingDrives: true,
      loadingApplicants: false,
      error: null,
      actionError: null,
      successMessage: null,
      drives: [],

      // null = show drive list; object = show applicants for that drive
      selectedDrive: null,
      applicants: [],

      // View Profile modal
      showProfileModal: false,
      profileApplicant: null,

      // Interview modal
      showInterviewModal: false,
      interviewApplicant: null,
      interviewForm: {
        interview_date: "",
        interview_time: "",
        interview_mode: "Online",
      },
      interviewError: null,

      // Per-row status dropdown values (keyed by application id)
      statusSelections: {},
      submitting: false,

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
    this.loadDrives();
  },

  methods: {
    /**
     * Step 1: fetch all drives so the company can pick one to review.
     */
    async loadDrives() {
      this.loadingDrives = true;
      this.error = null;

      try {
        this.drives = await getCompanyDrives();
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load placement drives. Please try again.";
      } finally {
        this.loadingDrives = false;
      }
    },

    /**
     * Step 2: user clicks "View Applicants" → load that drive's applications.
     */
    async viewApplicants(drive) {
      this.selectedDrive = drive;
      this.applicants = [];
      this.actionError = null;
      this.successMessage = null;
      await this.loadApplicants();
    },

    /**
     * Fetch applicants for the currently selected drive.
     */
    async loadApplicants() {
      if (!this.selectedDrive) {
        return;
      }

      this.loadingApplicants = true;
      this.actionError = null;

      try {
        const data = await getDriveApplications(this.selectedDrive.id);
        this.applicants = data;

        // Pre-fill status dropdowns with each applicant's current status
        const selections = {};
        for (const app of data) {
          selections[app.id] = app.status;
        }
        this.statusSelections = selections;
      } catch (err) {
        this.actionError =
          err.response?.data?.message ||
          "Failed to load applicants. Please try again.";
      } finally {
        this.loadingApplicants = false;
      }
    },

    backToDrives() {
      this.selectedDrive = null;
      this.applicants = [];
      this.actionError = null;
      this.successMessage = null;
    },

    // ---------- View Profile ----------

    openProfileModal(applicant) {
      this.profileApplicant = applicant;
      this.showProfileModal = true;
    },

    closeProfileModal() {
      this.showProfileModal = false;
      this.profileApplicant = null;
    },

    // ---------- Status update ----------

    /**
     * True when status dropdown and Update button should be disabled.
     * Rejected and Selected applications cannot be edited.
     */
    isStatusLocked(applicant) {
      return applicant.status === "Rejected" || applicant.status === "Selected";
    },

    /**
     * PUT /company/application/<id>/status → refresh table on success.
     */
    async handleStatusUpdate(applicant) {
      const newStatus = this.statusSelections[applicant.id];
      if (!newStatus || newStatus === applicant.status) {
        return;
      }

      this.submitting = true;
      this.actionError = null;
      this.successMessage = null;

      try {
        const result = await updateApplicationStatus(applicant.id, newStatus);
        this.successMessage =
          result.message || "Application status updated successfully.";
        await this.loadApplicants();
      } catch (err) {
        this.actionError =
          err.response?.data?.message ||
          "Failed to update status. Please try again.";
        // Reset dropdown to current server status
        this.statusSelections[applicant.id] = applicant.status;
      } finally {
        this.submitting = false;
      }
    },

    // ---------- Interview ----------

    /**
     * Interview button is shown for Shortlisted and Interview applicants.
     */
    canScheduleInterview(applicant) {
      return (
        applicant.status === "Shortlisted" || applicant.status === "Interview"
      );
    },

    openInterviewModal(applicant) {
      this.interviewApplicant = applicant;
      this.interviewError = null;
      this.interviewForm = {
        interview_date: applicant.interview_date || "",
        interview_time: applicant.interview_time || "",
        interview_mode: applicant.interview_mode || "Online",
      };
      this.showInterviewModal = true;
    },

    closeInterviewModal() {
      this.showInterviewModal = false;
      this.interviewApplicant = null;
      this.interviewError = null;
    },

    /**
     * PUT /company/application/<id>/interview → save date/time/mode.
     */
    async handleScheduleInterview() {
      this.submitting = true;
      this.interviewError = null;
      this.successMessage = null;

      try {
        const result = await scheduleApplicationInterview(
          this.interviewApplicant.id,
          this.interviewForm
        );
        this.successMessage =
          result.message || "Interview scheduled successfully.";
        this.closeInterviewModal();
        await this.loadApplicants();
      } catch (err) {
        this.interviewError =
          err.response?.data?.message ||
          "Failed to schedule interview. Please try again.";
      } finally {
        this.submitting = false;
      }
    },

    // ---------- Helpers ----------

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

    getDriveStatusBadgeClass(status) {
      if (status === "Pending") return "bg-warning text-dark";
      if (status === "Approved") return "bg-success";
      if (status === "Closed") return "bg-secondary";
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
  <div class="company-applicants">
    <!-- Top Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
      <span class="navbar-brand mb-0 h1">Company Dashboard</span>

      <div class="navbar-nav ms-auto flex-row align-items-center gap-2">
        <router-link class="nav-link text-light" to="/company">Dashboard</router-link>
        <router-link class="nav-link text-light" to="/company/drives">
          Placement Drives
        </router-link>
        <router-link class="nav-link text-light active" to="/company/applicants">
          Applicants
        </router-link>
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
            <router-link class="nav-link" to="/company/drives">
              Placement Drives
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link active" to="/company/applicants">
              Applicants
            </router-link>
          </li>
          <li class="nav-item">
            <span class="nav-link disabled text-muted">Profile</span>
          </li>
        </ul>
      </aside>

      <!-- Main Content -->
      <main class="flex-grow-1 p-4">
        <!-- Drive list view -->
        <div v-if="!selectedDrive">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="mb-0">Applicants</h2>
            <button
              type="button"
              class="btn btn-outline-secondary btn-sm"
              :disabled="loadingDrives"
              @click="loadDrives"
            >
              Refresh
            </button>
          </div>

          <p class="text-muted">
            Select a placement drive to view and manage its applicants.
          </p>

          <div v-if="loadingDrives" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">Loading placement drives...</p>
          </div>

          <div v-else-if="error" class="alert alert-warning" role="alert">
            {{ error }}
          </div>

          <div v-else class="card shadow-sm">
            <div class="card-body p-0">
              <table class="table table-striped table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th scope="col">Job Title</th>
                    <th scope="col">Eligible Branch</th>
                    <th scope="col">Deadline</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="drives.length === 0">
                    <td colspan="5" class="text-center text-muted py-4">
                      No placement drives found. Create a drive first.
                    </td>
                  </tr>
                  <tr v-for="drive in drives" :key="drive.id">
                    <td>{{ drive.title }}</td>
                    <td>{{ drive.eligible_branch }}</td>
                    <td>{{ formatDate(drive.deadline) }}</td>
                    <td>
                      <span
                        class="badge"
                        :class="getDriveStatusBadgeClass(drive.status)"
                      >
                        {{ drive.status }}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        class="btn btn-sm btn-primary"
                        @click="viewApplicants(drive)"
                      >
                        View Applicants
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Applicants table view -->
        <div v-else>
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div>
              <button
                type="button"
                class="btn btn-outline-secondary btn-sm me-2"
                @click="backToDrives"
              >
                &larr; Back to Drives
              </button>
              <h2 class="d-inline-block mb-0">
                Applicants — {{ selectedDrive.title }}
              </h2>
            </div>
            <button
              type="button"
              class="btn btn-outline-secondary btn-sm"
              :disabled="loadingApplicants"
              @click="loadApplicants"
            >
              Refresh
            </button>
          </div>

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

          <div v-if="loadingApplicants" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">Loading applicants...</p>
          </div>

          <div v-else class="card shadow-sm">
            <div class="card-body p-0">
              <table class="table table-striped table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th scope="col">Student</th>
                    <th scope="col">Branch</th>
                    <th scope="col">CGPA</th>
                    <th scope="col">Year</th>
                    <th scope="col">Skills</th>
                    <th scope="col">Resume</th>
                    <th scope="col">Applied Date</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="applicants.length === 0">
                    <td colspan="9" class="text-center text-muted py-4">
                      No applicants for this drive yet.
                    </td>
                  </tr>
                  <tr v-for="app in applicants" :key="app.id">
                    <td>{{ app.student_name }}</td>
                    <td>{{ app.branch }}</td>
                    <td>{{ app.cgpa ?? "-" }}</td>
                    <td>{{ app.year ?? "-" }}</td>
                    <td class="text-truncate" style="max-width: 120px">
                      {{ app.skills || "-" }}
                    </td>
                    <td>{{ app.resume_filename || "-" }}</td>
                    <td>{{ formatDate(app.applied_date) }}</td>
                    <td>
                      <span class="badge" :class="statusBadgeClass(app.status)">
                        {{ app.status }}
                      </span>
                    </td>
                    <td>
                      <div class="d-flex flex-wrap gap-1 align-items-center">
                        <button
                          type="button"
                          class="btn btn-sm btn-outline-info"
                          @click="openProfileModal(app)"
                        >
                          View Profile
                        </button>

                        <select
                          v-model="statusSelections[app.id]"
                          class="form-select form-select-sm"
                          style="width: auto"
                          :disabled="isStatusLocked(app) || submitting"
                        >
                          <option
                            v-for="status in statusOptions"
                            :key="status"
                            :value="status"
                          >
                            {{ status }}
                          </option>
                        </select>

                        <button
                          type="button"
                          class="btn btn-sm btn-outline-primary"
                          :disabled="
                            isStatusLocked(app) ||
                            submitting ||
                            statusSelections[app.id] === app.status
                          "
                          @click="handleStatusUpdate(app)"
                        >
                          Update
                        </button>

                        <button
                          v-if="canScheduleInterview(app)"
                          type="button"
                          class="btn btn-sm btn-outline-warning"
                          :disabled="submitting"
                          @click="openInterviewModal(app)"
                        >
                          Interview
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- View Profile Modal -->
    <div
      v-if="showProfileModal && profileApplicant"
      class="modal fade show d-block"
      tabindex="-1"
      style="background-color: rgba(0, 0, 0, 0.5)"
      @click.self="closeProfileModal"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Student Profile</h5>
            <button
              type="button"
              class="btn-close"
              @click="closeProfileModal"
            ></button>
          </div>
          <div class="modal-body">
            <dl class="row mb-0">
              <dt class="col-sm-4">Name</dt>
              <dd class="col-sm-8">{{ profileApplicant.student_name }}</dd>

              <dt class="col-sm-4">Email</dt>
              <dd class="col-sm-8">{{ profileApplicant.email }}</dd>

              <dt class="col-sm-4">Branch</dt>
              <dd class="col-sm-8">{{ profileApplicant.branch }}</dd>

              <dt class="col-sm-4">Year</dt>
              <dd class="col-sm-8">{{ profileApplicant.year ?? "-" }}</dd>

              <dt class="col-sm-4">CGPA</dt>
              <dd class="col-sm-8">{{ profileApplicant.cgpa ?? "-" }}</dd>

              <dt class="col-sm-4">Skills</dt>
              <dd class="col-sm-8">{{ profileApplicant.skills || "-" }}</dd>

              <dt class="col-sm-4">Resume</dt>
              <dd class="col-sm-8">
                {{ profileApplicant.resume_filename || "Not uploaded" }}
              </dd>

              <dt class="col-sm-4">Status</dt>
              <dd class="col-sm-8">
                <span
                  class="badge"
                  :class="statusBadgeClass(profileApplicant.status)"
                >
                  {{ profileApplicant.status }}
                </span>
              </dd>
            </dl>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              @click="closeProfileModal"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Interview Modal -->
    <div
      v-if="showInterviewModal && interviewApplicant"
      class="modal fade show d-block"
      tabindex="-1"
      style="background-color: rgba(0, 0, 0, 0.5)"
      @click.self="closeInterviewModal"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              Schedule Interview — {{ interviewApplicant.student_name }}
            </h5>
            <button
              type="button"
              class="btn-close"
              @click="closeInterviewModal"
            ></button>
          </div>

          <form @submit.prevent="handleScheduleInterview">
            <div class="modal-body">
              <div v-if="interviewError" class="alert alert-danger" role="alert">
                {{ interviewError }}
              </div>

              <div class="mb-3">
                <label for="interviewDate" class="form-label">Interview Date</label>
                <input
                  id="interviewDate"
                  v-model="interviewForm.interview_date"
                  type="date"
                  class="form-control"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="interviewTime" class="form-label">Interview Time</label>
                <input
                  id="interviewTime"
                  v-model="interviewForm.interview_time"
                  type="time"
                  class="form-control"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="interviewMode" class="form-label">Interview Mode</label>
                <select
                  id="interviewMode"
                  v-model="interviewForm.interview_mode"
                  class="form-select"
                  required
                >
                  <option value="Online">Online</option>
                  <option value="Offline">Offline</option>
                </select>
              </div>
            </div>

            <div class="modal-footer">
              <button
                type="button"
                class="btn btn-secondary"
                :disabled="submitting"
                @click="closeInterviewModal"
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

/* Bootstrap doesn't include an orange badge by default */
.bg-orange {
  background-color: #fd7e14;
}
</style>
