/**
 * router/index.js - Vue Router Configuration
 *
 * Vue Router handles page navigation in a Single Page Application (SPA).
 * Each route maps a URL path to a Vue component (view).
 */

import { createRouter, createWebHistory } from "vue-router";
import { getRole, isLoggedIn } from "../services/api.js";
import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import StudentRegister from "../views/StudentRegister.vue";
import CompanyRegister from "../views/CompanyRegister.vue";
import AdminDashboard from "../views/AdminDashboard.vue";
import Companies from "../views/Companies.vue";
import PlacementDrives from "../views/PlacementDrives.vue";
import StudentDashboard from "../views/StudentDashboard.vue";
import CompanyDashboard from "../views/CompanyDashboard.vue";

// Define all routes for the application
const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
  },
  {
    path: "/register/student",
    name: "StudentRegister",
    component: StudentRegister,
  },
  {
    path: "/register/company",
    name: "CompanyRegister",
    component: CompanyRegister,
  },
  {
    path: "/admin",
    name: "AdminDashboard",
    component: AdminDashboard,
    meta: { requiresAdmin: true },
  },
  {
    path: "/admin/companies",
    name: "Companies",
    component: Companies,
    meta: { requiresAdmin: true },
  },
  {
    path: "/admin/drives",
    name: "PlacementDrives",
    component: PlacementDrives,
    meta: { requiresAdmin: true },
  },
  {
    path: "/student",
    name: "StudentDashboard",
    component: StudentDashboard,
  },
  {
    path: "/company",
    name: "CompanyDashboard",
    component: CompanyDashboard,
  },
];

// Create the router instance
const router = createRouter({
  // Use HTML5 history mode (clean URLs without #)
  history: createWebHistory(),
  routes,
});

// Protect admin dashboard: only logged-in admin users can access /admin
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAdmin) {
    if (!isLoggedIn() || getRole() !== "admin") {
      next({ name: "Login" });
      return;
    }
  }
  next();
});

export default router;
