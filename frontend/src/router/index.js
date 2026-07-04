/**
 * router/index.js - Vue Router Configuration
 *
 * Vue Router handles page navigation in a Single Page Application (SPA).
 * Each route maps a URL path to a Vue component (view).
 */

import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";

// Define all routes for the application
const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
  },
];

// Create the router instance
const router = createRouter({
  // Use HTML5 history mode (clean URLs without #)
  history: createWebHistory(),
  routes,
});

export default router;
