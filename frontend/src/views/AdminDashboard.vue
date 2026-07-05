<script setup>
/**
 * AdminDashboard.vue - Temporary placeholder for admin users.
 */

import { useRouter } from "vue-router";
import { clearAuthData, logout } from "../services/api.js";

const router = useRouter();

async function handleLogout() {
  try {
    await logout();
  } catch (error) {
    console.error("Logout error:", error);
  }

  clearAuthData();
  router.push("/login");
}
</script>

<template>
  <div class="container py-5 text-center">
    <h1>Welcome Admin</h1>
    <p class="text-muted mb-4">This is a temporary dashboard placeholder.</p>
    <button type="button" class="btn btn-danger" @click="handleLogout">
      Logout
    </button>
  </div>
</template>
