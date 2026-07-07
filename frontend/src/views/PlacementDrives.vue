<script>
/**
 * PlacementDrives.vue - Admin Placement Drive Approval Page (Stage 4.2)
 *
 * Lists all placement drives in a Bootstrap table.
 * Admin can Approve or Reject each drive after confirmation.
 * Table refreshes automatically after each action.
 */

import {
  fetchDrives,
  approveDrive,
  rejectDrive,
} from "../services/api.js";

export default {
  name: "PlacementDrives",

  data() {
    return {
      loading: true,
      error: null,
      drives: [],
      actionLoading: false,
    };
  },

  mounted() {
    this.loadDrives();
  },

  methods: {
    /** Fetch all drives from GET /admin/drives */
    async loadDrives() {
      this.loading = true;
      this.error = null;

      try {
        this.drives = await fetchDrives();
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load placement drives. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    /** Show confirmation dialog, then approve the drive */
    async handleApprove(drive) {
      const confirmed = window.confirm(
        `Approve placement drive "${drive.drive_title}"?`
      );
      if (!confirmed) {
        return;
      }

      this.actionLoading = true;

      try {
        await approveDrive(drive.id);
        await this.loadDrives();
      } catch (err) {
        alert(
          err.response?.data?.message ||
            "Failed to approve drive. Please try again."
        );
      } finally {
        this.actionLoading = false;
      }
    },

    /** Show confirmation dialog, then reject the drive */
    async handleReject(drive) {
      const confirmed = window.confirm(
        `Reject placement drive "${drive.drive_title}"?`
      );
      if (!confirmed) {
        return;
      }

      this.actionLoading = true;

      try {
        await rejectDrive(drive.id);
        await this.loadDrives();
      } catch (err) {
        alert(
          err.response?.data?.message ||
            "Failed to reject drive. Please try again."
        );
      } finally {
        this.actionLoading = false;
      }
    },

    /** Return Bootstrap badge class based on drive status */
    statusBadgeClass(status) {
      if (status === "Approved") {
        return "bg-success";
      }
      if (status === "Rejected") {
        return "bg-danger";
      }
      return "bg-warning text-dark";
    },

    formatDate(dateString) {
      if (!dateString) {
        return "-";
      }
      return new Date(dateString).toLocaleDateString();
    },
  },
};
</script>

<template>
  <div class="admin-dashboard">
    <nav class="navbar navbar-dark bg-dark px-3">
      <span class="navbar-brand mb-0 h1">Admin Dashboard</span>
      <span class="text-light small">Placement Portal</span>
    </nav>

    <div class="d-flex admin-layout">
      <aside class="sidebar bg-light border-end p-3">
        <h6 class="text-muted text-uppercase small mb-3">Menu</h6>
        <ul class="nav flex-column">
          <li class="nav-item">
            <router-link class="nav-link" to="/admin">Dashboard</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/companies">
              Companies
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link active" to="/admin/drives">
              Placement Drives
            </router-link>
          </li>
        </ul>
      </aside>

      <main class="flex-grow-1 p-4">
        <h2 class="mb-4">Placement Drive Approval</h2>

        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading placement drives...</p>
        </div>

        <div v-else-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>

        <div v-else class="card shadow-sm">
          <div class="card-body p-0">
            <table class="table table-striped table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">Company</th>
                  <th scope="col">Deadline</th>
                  <th scope="col">Status</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="drives.length === 0">
                  <td colspan="5" class="text-center text-muted">
                    No placement drives found.
                  </td>
                </tr>
                <tr v-for="drive in drives" :key="drive.id">
                  <td>{{ drive.drive_title }}</td>
                  <td>{{ drive.company }}</td>
                  <td>{{ formatDate(drive.deadline) }}</td>
                  <td>
                    <span
                      class="badge"
                      :class="statusBadgeClass(drive.status)"
                    >
                      {{ drive.status }}
                    </span>
                  </td>
                  <td>
                    <button
                      class="btn btn-sm btn-success me-2"
                      :disabled="actionLoading || drive.status === 'Approved'"
                      @click="handleApprove(drive)"
                    >
                      Approve
                    </button>
                    <button
                      class="btn btn-sm btn-danger"
                      :disabled="actionLoading || drive.status === 'Rejected'"
                      @click="handleReject(drive)"
                    >
                      Reject
                    </button>
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
