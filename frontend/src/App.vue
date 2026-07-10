<script setup>
/**
 * App.vue - Root Component
 *
 * Shows the public Navbar on unauthenticated pages.
 * Dashboard views have their own navigation — hide the global Navbar there.
 */
import { computed } from "vue";
import { useRoute } from "vue-router";
import Navbar from "./components/Navbar.vue";

const route = useRoute();

const showGlobalNavbar = computed(() => !route.meta.hideGlobalNavbar);
</script>

<template>
  <Navbar v-if="showGlobalNavbar" />

  <!-- Vue Router renders the matched page component here -->
  <router-view />
</template>
