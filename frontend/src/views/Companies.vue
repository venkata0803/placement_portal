<script>
/**
 * Companies.vue - Admin Company Approval Page (Stage 4.2)
 *
 * Lists all registered companies in a Bootstrap table.
 * Admin can Approve or Reject each company after confirmation.
 * Table refreshes automatically after each action.
 */

import {
  fetchCompanies,
  approveCompany,
  rejectCompany,
} from "../services/api.js";

export default {
  name: "Companies",

  data() {
    return {
      loading: true,
      error: null,
      companies: [],
      actionLoading: false,
    };
  },

  mounted() {
    this.loadCompanies();
  },

  methods: {
    /** Fetch all companies from GET /admin/companies */
    async loadCompanies() {
      this.loading = true;
      this.error = null;

      try {
        this.companies = await fetchCompanies();
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          "Failed to load companies. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    /** Show confirmation dialog, then approve the company */
    async handleApprove(company) {
      const confirmed = window.confirm(
        `Approve company "${company.company_name}"?`
      );
      if (!confirmed) {
        return;
      }

      this.actionLoading = true;

      try {
        await approveCompany(company.id);
        await this.loadCompanies();
      } catch (err) {
        alert(
          err.response?.data?.message ||
            "Failed to approve company. Please try again."
        );
      } finally {
        this.actionLoading = false;
      }
    },

    /** Show confirmation dialog, then reject the company */
    async handleReject(company) {
      const confirmed = window.confirm(
        `Reject company "${company.company_name}"?`
      );
      if (!confirmed) {
        return;
      }

      this.actionLoading = true;

      try {
        await rejectCompany(company.id);
        await this.loadCompanies();
      } catch (err) {
        alert(
          err.response?.data?.message ||
            "Failed to reject company. Please try again."
        );
      } finally {
        this.actionLoading = false;
      }
    },

    /** Return Bootstrap badge class based on approval status */
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
            <router-link class="nav-link active" to="/admin/companies">
              Companies
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/admin/drives">
              Placement Drives
            </router-link>
          </li>
        </ul>
      </aside>

      <main class="flex-grow-1 p-4">
        <h2 class="mb-4">Company Approval</h2>

        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading companies...</p>
        </div>

        <div v-else-if="error" class="alert alert-danger" role="alert">
          {{ error }}
        </div>

        <div v-else class="card shadow-sm">
          <div class="card-body p-0">
            <table class="table table-striped table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th scope="col">Company Name</th>
                  <th scope="col">Email</th>
                  <th scope="col">Website</th>
                  <th scope="col">Status</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="companies.length === 0">
                  <td colspan="5" class="text-center text-muted">
                    No companies registered yet.
                  </td>
                </tr>
                <tr v-for="company in companies" :key="company.id">
                  <td>{{ company.company_name }}</td>
                  <td>{{ company.email }}</td>
                  <td>{{ company.website || "-" }}</td>
                  <td>
                    <span
                      class="badge"
                      :class="statusBadgeClass(company.approval_status)"
                    >
                      {{ company.approval_status }}
                    </span>
                  </td>
                  <td>
                    <button
                      class="btn btn-sm btn-success me-2"
                      :disabled="actionLoading || company.approval_status === 'Approved'"
                      @click="handleApprove(company)"
                    >
                      Approve
                    </button>
                    <button
                      class="btn btn-sm btn-danger"
                      :disabled="actionLoading || company.approval_status === 'Rejected'"
                      @click="handleReject(company)"
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
