<script setup>
/**
 * App.vue - Root Component
 *
 * Shows the Navbar on every page and renders the current route below it.
 */
import Navbar from "./components/Navbar.vue";
</script>

<template>
  <!-- Navigation bar appears on all pages -->
  <Navbar />

  <!-- Vue Router renders the matched page component here -->
  <router-view />
</template>
