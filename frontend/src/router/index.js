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
import Students from "../views/Students.vue";
import Companies from "../views/Companies.vue";
import PlacementDrives from "../views/PlacementDrives.vue";
import AdminApplications from "../views/AdminApplications.vue";
import AdminProfile from "../views/AdminProfile.vue";
import StudentDashboard from "../views/StudentDashboard.vue";
import StudentProfile from "../views/StudentProfile.vue";
import BrowsePlacementDrives from "../views/BrowsePlacementDrives.vue";
import MyApplications from "../views/MyApplications.vue";
import CompanyDashboard from "../views/CompanyDashboard.vue";
import CompanyPlacementDrives from "../views/company/PlacementDrives.vue";
import CompanyApplicants from "../views/company/CompanyApplicants.vue";
import CompanyProfile from "../views/company/CompanyProfile.vue";

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
    meta: { requiresAdmin: true, hideGlobalNavbar: true },
  },
  {
    path: "/admin/students",
    name: "Students",
    component: Students,
    meta: { requiresAdmin: true, hideGlobalNavbar: true },
  },
  {
    path: "/admin/companies",
    name: "Companies",
    component: Companies,
    meta: { requiresAdmin: true, hideGlobalNavbar: true },
  },
  {
    path: "/admin/drives",
    name: "PlacementDrives",
    component: PlacementDrives,
    meta: { requiresAdmin: true, hideGlobalNavbar: true },
  },
  {
    path: "/admin/applications",
    name: "AdminApplications",
    component: AdminApplications,
    meta: { requiresAdmin: true, hideGlobalNavbar: true },
  },
  {
    path: "/admin/profile",
    name: "AdminProfile",
    component: AdminProfile,
    meta: { requiresAdmin: true, hideGlobalNavbar: true },
  },
  {
    path: "/student",
    name: "StudentDashboard",
    component: StudentDashboard,
    meta: { requiresStudent: true, hideGlobalNavbar: true },
  },
  {
    path: "/student/profile",
    name: "StudentProfile",
    component: StudentProfile,
    meta: { requiresStudent: true, hideGlobalNavbar: true },
  },
  {
    path: "/student/drives",
    name: "BrowsePlacementDrives",
    component: BrowsePlacementDrives,
    meta: { requiresStudent: true, hideGlobalNavbar: true },
  },
  {
    path: "/student/applications",
    name: "MyApplications",
    component: MyApplications,
    meta: { requiresStudent: true, hideGlobalNavbar: true },
  },
  {
    path: "/company",
    name: "CompanyDashboard",
    component: CompanyDashboard,
    meta: { requiresCompany: true, hideGlobalNavbar: true },
  },
  {
    path: "/company/drives",
    name: "CompanyPlacementDrives",
    component: CompanyPlacementDrives,
    meta: { requiresCompany: true, hideGlobalNavbar: true },
  },
  {
    path: "/company/applicants",
    name: "CompanyApplicants",
    component: CompanyApplicants,
    meta: { requiresCompany: true, hideGlobalNavbar: true },
  },
  {
    path: "/company/profile",
    name: "CompanyProfile",
    component: CompanyProfile,
    meta: { requiresCompany: true, hideGlobalNavbar: true },
  },
];

// Create the router instance
const router = createRouter({
  // Use HTML5 history mode (clean URLs without #)
  history: createWebHistory(),
  routes,
});

// Protect role-specific routes: redirect to Login if not allowed
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAdmin) {
    if (!isLoggedIn() || getRole() !== "admin") {
      next({ name: "Login" });
      return;
    }
  }

  if (to.meta.requiresCompany) {
    if (!isLoggedIn() || getRole() !== "company") {
      next({ name: "Login" });
      return;
    }
  }

  // Stage 6.1: only authenticated Student users can open /student
  if (to.meta.requiresStudent) {
    if (!isLoggedIn() || getRole() !== "student") {
      next({ name: "Login" });
      return;
    }
  }

  next();
});

export default router;
