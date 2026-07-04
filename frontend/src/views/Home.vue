<script setup>
/**
 * Home.vue - Main page of the Placement Portal
 *
 * This page shows:
 * 1. Application title
 * 2. Backend connection status
 * 3. A button to check the backend again
 */

import { ref, onMounted } from "vue";
import { checkBackendStatus } from "../services/api.js";

// Reactive variable to store the message from the backend
const backendMessage = ref("Checking backend...");

// Reactive variable to show if the backend is online or offline
const isBackendOnline = ref(false);

// Function to call the backend API and update the status
async function fetchBackendStatus() {
  backendMessage.value = "Checking backend...";
  isBackendOnline.value = false;

  try {
    // Call our API service (defined in services/api.js)
    const response = await checkBackendStatus();
    backendMessage.value = response.message;
    isBackendOnline.value = true;
  } catch (error) {
    // If the backend is not running, show an error message
    backendMessage.value = "Backend is offline. Start the Flask server first.";
    isBackendOnline.value = false;
  }
}

// When the page loads, automatically check backend status
onMounted(() => {
  fetchBackendStatus();
});
</script>

<template>
  <div class="container py-5">
    <!-- Page title -->
    <h1 class="text-center mb-4">Placement Portal Application</h1>

    <!-- Backend status card -->
    <div class="card mx-auto" style="max-width: 500px">
      <div class="card-body text-center">
        <h5 class="card-title">Backend Status</h5>

        <!-- Green badge if online, red if offline -->
        <span
          class="badge mb-3"
          :class="isBackendOnline ? 'bg-success' : 'bg-danger'"
        >
          {{ isBackendOnline ? "Online" : "Offline" }}
        </span>

        <p class="card-text">{{ backendMessage }}</p>

        <!-- Bootstrap button to re-check backend status -->
        <button
          type="button"
          class="btn btn-primary"
          @click="fetchBackendStatus"
        >
          Check Backend Again
        </button>
      </div>
    </div>
  </div>
</template>
