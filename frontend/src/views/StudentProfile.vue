<script>
/**
 * StudentProfile.vue - Student Profile Management (Stage 6.2)
 *
 * Frontend Flow
 * -------------
 * 1. Router guard ensures only Students can open /student/profile
 * 2. On mount, GET /student/profile loads current data into the form
 * 3. Save Changes → PUT /student/profile (editable fields only)
 * 4. Upload Resume → POST /student/upload-resume (multipart PDF)
 *
 * Branch and Year are read-only (set at registration).
 */

import {
  clearAuthData,
  getStudentProfile,
  logout,
  updateStudentProfile,
  uploadStudentResume,
} from "../services/api.js";

export default {
  name: "StudentProfile",

  data() {
    return {
      loading: true,
      saving: false,
      uploading: false,
      error: null,
      success: null,
      uploadError: null,
      uploadSuccess: null,
      // Form fields
      fullName: "",
      email: "",
      phone: "",
      branch: "",
      cgpa: "",
      year: "",
      skills: "",
      resumeFilename: null,
      // Selected file from <input type="file">
      selectedFile: null,
    };
  },

  mounted() {
    this.fetchProfile();
  },

  methods: {
    /**
     * Load profile from GET /student/profile.
     */
    async fetchProfile() {
      this.loading = true;
      this.error = null;

      try {
        const data = await getStudentProfile();
        this.applyProfileData(data);
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load profile. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    /**
     * Copy API response fields into the form.
     */
    applyProfileData(data) {
      this.fullName = data.full_name || "";
      this.email = data.email || "";
      this.phone = data.phone || "";
      this.branch = data.branch || "";
      this.cgpa = data.cgpa;
      this.year = data.year;
      this.skills = data.skills || "";
      this.resumeFilename = data.resume_filename;
    },

    /**
     * Frontend validation before Save Changes.
     * Backend repeats the same checks.
     */
    validateForm() {
      if (!this.fullName || !this.fullName.trim()) {
        return "Full name is required";
      }
      if (!this.phone || !this.phone.trim()) {
        return "Phone is required";
      }
      if (this.cgpa === "" || this.cgpa === null) {
        return "CGPA is required";
      }
      const cgpaNumber = Number(this.cgpa);
      if (Number.isNaN(cgpaNumber)) {
        return "CGPA must be a valid number";
      }
      if (cgpaNumber < 0 || cgpaNumber > 10) {
        return "CGPA must be between 0 and 10";
      }
      return null;
    },

    /**
     * Save editable profile fields via PUT /student/profile.
     */
    async handleSave() {
      this.error = null;
      this.success = null;
      this.uploadError = null;
      this.uploadSuccess = null;

      const validationError = this.validateForm();
      if (validationError) {
        this.error = validationError;
        return;
      }

      this.saving = true;

      try {
        const response = await updateStudentProfile({
          full_name: this.fullName.trim(),
          phone: this.phone.trim(),
          cgpa: Number(this.cgpa),
          skills: this.skills.trim(),
        });

        this.success = response.message || "Profile updated successfully";
        if (response.profile) {
          this.applyProfileData(response.profile);
        }
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to update profile. Please try again.";
      } finally {
        this.saving = false;
      }
    },

    /**
     * Remember the file chosen in the file input.
     */
    onFileChange(event) {
      const file = event.target.files[0] || null;
      this.selectedFile = file;
      this.uploadError = null;
      this.uploadSuccess = null;

      // Quick frontend check: PDF only
      if (file && !file.name.toLowerCase().endsWith(".pdf")) {
        this.uploadError = "Only PDF files are allowed";
        this.selectedFile = null;
        event.target.value = "";
      }
    },

    /**
     * Upload resume via POST /student/upload-resume (FormData).
     */
    async handleUploadResume() {
      this.uploadError = null;
      this.uploadSuccess = null;
      this.error = null;
      this.success = null;

      if (!this.selectedFile) {
        this.uploadError = "Please select a PDF file to upload";
        return;
      }

      if (!this.selectedFile.name.toLowerCase().endsWith(".pdf")) {
        this.uploadError = "Only PDF files are allowed";
        return;
      }

      // 5 MB = 5 * 1024 * 1024 bytes
      if (this.selectedFile.size > 5 * 1024 * 1024) {
        this.uploadError = "Resume must be 5 MB or smaller";
        return;
      }

      this.uploading = true;

      try {
        const response = await uploadStudentResume(this.selectedFile);
        this.uploadSuccess =
          response.message || "Resume uploaded successfully";
        this.resumeFilename = response.resume_filename;
        this.selectedFile = null;

        // Clear the file input so the same file can be re-selected if needed
        if (this.$refs.resumeInput) {
          this.$refs.resumeInput.value = "";
        }
      } catch (err) {
        this.uploadError =
          err.response?.data?.message ||
          "Failed to upload resume. Please try again.";
      } finally {
        this.uploading = false;
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
  <div class="student-profile">
    <!-- Top Navbar -->
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
      <!-- Sidebar -->
      <aside class="sidebar bg-light border-end p-3">
        <h6 class="text-muted text-uppercase small mb-3">Menu</h6>
        <ul class="nav flex-column">
          <li class="nav-item">
            <router-link class="nav-link" to="/student">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/student/drives">
              Browse Drives
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/student/applications">
              My Applications
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link active" to="/student/profile">
              Profile
            </router-link>
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
        <h2 class="mb-4">My Profile</h2>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading profile...</p>
        </div>

        <div v-else class="row justify-content-center">
          <div class="col-lg-8">
            <!-- Profile form card -->
            <div class="card shadow-sm mb-4">
              <div class="card-header">
                <h5 class="mb-0">Edit Profile</h5>
              </div>
              <div class="card-body">
                <div v-if="error" class="alert alert-danger" role="alert">
                  {{ error }}
                </div>
                <div v-if="success" class="alert alert-success" role="alert">
                  {{ success }}
                </div>

                <form @submit.prevent="handleSave">
                  <div class="mb-3">
                    <label class="form-label">Full Name</label>
                    <input
                      v-model="fullName"
                      type="text"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="mb-3">
                    <label class="form-label">Email</label>
                    <input
                      :value="email"
                      type="email"
                      class="form-control"
                      readonly
                      disabled
                    />
                    <div class="form-text">Email cannot be changed here.</div>
                  </div>

                  <div class="mb-3">
                    <label class="form-label">Phone</label>
                    <input
                      v-model="phone"
                      type="text"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Branch</label>
                      <input
                        :value="branch"
                        type="text"
                        class="form-control"
                        readonly
                        disabled
                      />
                      <div class="form-text">Read only</div>
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Year</label>
                      <input
                        :value="year"
                        type="text"
                        class="form-control"
                        readonly
                        disabled
                      />
                      <div class="form-text">Read only</div>
                    </div>
                  </div>

                  <div class="mb-3">
                    <label class="form-label">CGPA</label>
                    <input
                      v-model="cgpa"
                      type="number"
                      class="form-control"
                      min="0"
                      max="10"
                      step="0.01"
                      required
                    />
                    <div class="form-text">Must be between 0 and 10</div>
                  </div>

                  <div class="mb-3">
                    <label class="form-label">Skills</label>
                    <textarea
                      v-model="skills"
                      class="form-control"
                      rows="3"
                      placeholder="e.g. Python, SQL, Vue.js"
                    ></textarea>
                  </div>

                  <button
                    type="submit"
                    class="btn btn-primary"
                    :disabled="saving"
                  >
                    <span
                      v-if="saving"
                      class="spinner-border spinner-border-sm me-1"
                      role="status"
                    ></span>
                    {{ saving ? "Saving..." : "Save Changes" }}
                  </button>
                </form>
              </div>
            </div>

            <!-- Resume upload card -->
            <div class="card shadow-sm">
              <div class="card-header">
                <h5 class="mb-0">Resume Upload</h5>
              </div>
              <div class="card-body">
                <div v-if="uploadError" class="alert alert-danger" role="alert">
                  {{ uploadError }}
                </div>
                <div
                  v-if="uploadSuccess"
                  class="alert alert-success"
                  role="alert"
                >
                  {{ uploadSuccess }}
                </div>

                <p class="mb-2">
                  <strong>Current resume:</strong>
                  <span v-if="resumeFilename">{{ resumeFilename }}</span>
                  <span v-else class="text-muted">No resume uploaded yet</span>
                </p>

                <div class="mb-3">
                  <label class="form-label">Select PDF (max 5 MB)</label>
                  <input
                    ref="resumeInput"
                    type="file"
                    class="form-control"
                    accept=".pdf,application/pdf"
                    @change="onFileChange"
                  />
                </div>

                <button
                  type="button"
                  class="btn btn-success"
                  :disabled="uploading"
                  @click="handleUploadResume"
                >
                  <span
                    v-if="uploading"
                    class="spinner-border spinner-border-sm me-1"
                    role="status"
                  ></span>
                  {{ uploading ? "Uploading..." : "Upload Resume" }}
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
</style>
