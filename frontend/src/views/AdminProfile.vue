<script>
/**
 * AdminProfile.vue - Admin Profile Page
 *
 * View: Name, Email, Role, Created Date
 * Edit: Name, Password, Email (optional)
 */

import {
  clearAuthData,
  getAdminProfile,
  logout,
  updateAdminProfile,
} from "../services/api.js";

export default {
  name: "AdminProfile",

  data() {
    return {
      loading: true,
      saving: false,
      error: null,
      success: null,
      name: "",
      email: "",
      role: "",
      createdAt: "",
      password: "",
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
        const data = await getAdminProfile();
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
      this.name = data.name || "";
      this.email = data.email || "";
      this.role = data.role || "";
      this.createdAt = data.created_at || "";
      this.password = "";
    },

    validateForm() {
      if (!this.name || !this.name.trim()) {
        return "Name is required";
      }
      if (this.password && this.password.length < 6) {
        return "Password must be at least 6 characters";
      }
      if (this.email && this.email.trim() && !this.email.includes("@")) {
        return "Please enter a valid email";
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
        const payload = {
          name: this.name.trim(),
          email: this.email.trim(),
        };
        if (this.password && this.password.trim()) {
          payload.password = this.password;
        }

        const response = await updateAdminProfile(payload);
        this.success = response.message || "Profile updated successfully";
        if (response.profile) {
          this.applyProfileData(response.profile);
        }
        if (response.profile?.name) {
          localStorage.setItem("username", response.profile.name);
        }
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to update profile. Please try again.";
      } finally {
        this.saving = false;
      }
    },

    formatDate(dateString) {
      if (!dateString) {
        return "-";
      }
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
            <router-link class="nav-link" to="/admin/applications">
              Applications
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link active" to="/admin/profile">
              Profile
            </router-link>
          </li>
        </ul>
      </aside>

      <main class="flex-grow-1 p-4">
        <h2 class="mb-4">Admin Profile</h2>

        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading profile...</p>
        </div>

        <div v-else class="row justify-content-center">
          <div class="col-lg-8">
            <div class="card shadow-sm mb-4">
              <div class="card-header">
                <h5 class="mb-0">Account Details</h5>
              </div>
              <div class="card-body">
                <dl class="row mb-0">
                  <dt class="col-sm-3">Role</dt>
                  <dd class="col-sm-9">
                    <span class="badge bg-dark">{{ role }}</span>
                  </dd>
                  <dt class="col-sm-3">Created Date</dt>
                  <dd class="col-sm-9">{{ formatDate(createdAt) }}</dd>
                </dl>
              </div>
            </div>

            <div class="card shadow-sm">
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
                    <label class="form-label">Name</label>
                    <input
                      v-model="name"
                      type="text"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="mb-3">
                    <label class="form-label">Email</label>
                    <input
                      v-model="email"
                      type="email"
                      class="form-control"
                    />
                    <div class="form-text">Optional — leave unchanged if not needed.</div>
                  </div>

                  <div class="mb-3">
                    <label class="form-label">New Password</label>
                    <input
                      v-model="password"
                      type="password"
                      class="form-control"
                      autocomplete="new-password"
                      placeholder="Leave blank to keep current password"
                    />
                    <div class="form-text">Minimum 6 characters if changing.</div>
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
