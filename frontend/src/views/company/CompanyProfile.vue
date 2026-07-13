<script>
/**
 * CompanyProfile.vue - Company Profile Management
 *
 * Load, edit, and save company profile details.
 */

import {
  clearAuthData,
  getCompanyProfile,
  logout,
  updateCompanyProfile,
} from "../../services/api.js";

export default {
  name: "CompanyProfile",

  data() {
    return {
      loading: true,
      saving: false,
      error: null,
      success: null,
      companyName: "",
      website: "",
      industry: "",
      location: "",
      hrName: "",
      hrEmail: "",
      description: "",
      approvalStatus: "",
    };
  },

  mounted() {
    this.fetchProfile();
  },

  methods: {
    async fetchProfile() {
      this.loading = true;
      this.error = null;

      try {
        const data = await getCompanyProfile();
        this.applyProfileData(data);
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load profile. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    applyProfileData(data) {
      this.companyName = data.company_name || "";
      this.website = data.website || "";
      this.industry = data.industry || "";
      this.location = data.location || "";
      this.hrName = data.hr_name || "";
      this.hrEmail = data.hr_email || "";
      this.description = data.description || "";
      this.approvalStatus = data.approval_status || "";
    },

    validateForm() {
      if (!this.companyName || !this.companyName.trim()) {
        return "Company name is required";
      }
      if (!this.hrName || !this.hrName.trim()) {
        return "HR name is required";
      }
      if (!this.hrEmail || !this.hrEmail.trim()) {
        return "HR email is required";
      }
      if (!this.hrEmail.includes("@")) {
        return "Please enter a valid HR email";
      }
      return null;
    },

    async handleSave() {
      this.error = null;
      this.success = null;

      const validationError = this.validateForm();
      if (validationError) {
        this.error = validationError;
        return;
      }

      this.saving = true;

      try {
        const response = await updateCompanyProfile({
          company_name: this.companyName.trim(),
          website: this.website.trim(),
          industry: this.industry.trim(),
          location: this.location.trim(),
          hr_name: this.hrName.trim(),
          hr_email: this.hrEmail.trim(),
          description: this.description.trim(),
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
  <div class="company-profile">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-3">
      <span class="navbar-brand mb-0 h1">Company Dashboard</span>

      <div class="navbar-nav ms-auto flex-row align-items-center gap-2">
        <router-link class="nav-link text-light" to="/company">Dashboard</router-link>
        <router-link class="nav-link text-light" to="/company/drives">
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
            <router-link class="nav-link" to="/company/applicants">
              Applicants
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link active" to="/company/profile">
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

      <main class="flex-grow-1 p-4">
        <h2 class="mb-4">Company Profile</h2>

        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading profile...</p>
        </div>

        <div v-else class="row justify-content-center">
          <div class="col-lg-8">
            <div class="card shadow-sm">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">Edit Profile</h5>
                <span
                  class="badge"
                  :class="{
                    'bg-success': approvalStatus === 'Approved',
                    'bg-warning text-dark': approvalStatus === 'Pending',
                    'bg-danger': approvalStatus === 'Rejected',
                    'bg-secondary': !approvalStatus,
                  }"
                >
                  {{ approvalStatus || "Unknown" }}
                </span>
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
                    <label class="form-label">Company Name</label>
                    <input
                      v-model="companyName"
                      type="text"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="mb-3">
                    <label class="form-label">Website</label>
                    <input
                      v-model="website"
                      type="text"
                      class="form-control"
                      placeholder="https://example.com"
                    />
                  </div>

                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Industry</label>
                      <input
                        v-model="industry"
                        type="text"
                        class="form-control"
                        placeholder="e.g. Information Technology"
                      />
                    </div>
                    <div class="col-md-6 mb-3">
                      <label class="form-label">Location</label>
                      <input
                        v-model="location"
                        type="text"
                        class="form-control"
                        placeholder="e.g. Bangalore"
                      />
                    </div>
                  </div>

                  <div class="mb-3">
                    <label class="form-label">HR Name</label>
                    <input
                      v-model="hrName"
                      type="text"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="mb-3">
                    <label class="form-label">HR Email</label>
                    <input
                      v-model="hrEmail"
                      type="email"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="mb-3">
                    <label class="form-label">Description</label>
                    <textarea
                      v-model="description"
                      class="form-control"
                      rows="4"
                      placeholder="Brief company description"
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
          </div>
        </div>
      </main>
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
