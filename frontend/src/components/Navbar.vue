<script setup>
/**
 * Navbar.vue - Simple Bootstrap Navigation Bar
 *
 * Shows links for Home, Register, Login, and Logout.
 * Logout is shown only when the user is logged in.
 */

import { computed } from "vue";
import { useRouter } from "vue-router";
import { clearAuthData, isLoggedIn, logout } from "../services/api.js";

const router = useRouter();

// Reactive check: is user currently logged in?
const loggedIn = computed(() => isLoggedIn());

// Handle logout button click
async function handleLogout() {
  try {
    // Tell backend we are logging out (optional, token removed on client)
    await logout();
  } catch (error) {
    // Even if API fails, still clear local storage
    console.error("Logout error:", error);
  }

  // Remove token and user info from browser storage
  clearAuthData();

  // Redirect to login page
  router.push("/login");
}
</script>

<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
      <router-link class="navbar-brand" to="/">Placement Portal</router-link>

      <div class="navbar-nav ms-auto">
        <router-link class="nav-link" to="/">Home</router-link>
        <router-link class="nav-link" to="/register/student">
          Student Register
        </router-link>
        <router-link class="nav-link" to="/register/company">
          Company Register
        </router-link>
        <router-link class="nav-link" to="/login">Login</router-link>

        <!-- Show Logout only when user has a token -->
        <button
          v-if="loggedIn"
          type="button"
          class="nav-link btn btn-link text-white"
          @click="handleLogout"
        >
          Logout
        </button>
      </div>
    </div>
  </nav>
</template>
