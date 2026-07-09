/**
 * services/api.js - API Service
 *
 * This file handles all HTTP requests to the Flask backend.
 * We use Axios to send GET, POST, PUT, DELETE requests.
 *
 * Authentication:
 * - After login, JWT token is stored in localStorage
 * - Axios automatically attaches the token to every request
 */

import axios from "axios";

// Base URL of the Flask backend server
const API_BASE_URL = "http://localhost:5000";

// Create an Axios instance with default settings
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Attach JWT token to every API request (if user is logged in).
 * Header format: Authorization: Bearer <token>
 */
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------- Auth helper functions ----------

export function saveAuthData(token, role, username) {
  localStorage.setItem("token", token);
  localStorage.setItem("role", role);
  localStorage.setItem("username", username);
}

export function clearAuthData() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
}

export function isLoggedIn() {
  return !!localStorage.getItem("token");
}

export function getRole() {
  return localStorage.getItem("role");
}

// ---------- API calls ----------

export async function checkBackendStatus() {
  const response = await apiClient.get("/");
  return response.data;
}

export async function registerStudent(studentData) {
  const response = await apiClient.post("/register/student", studentData);
  return response.data;
}

export async function registerCompany(companyData) {
  const response = await apiClient.post("/register/company", companyData);
  return response.data;
}

export async function login(email, password) {
  const response = await apiClient.post("/login", { email, password });
  return response.data;
}

export async function logout() {
  const response = await apiClient.post("/logout");
  return response.data;
}

export async function getCurrentUser() {
  const response = await apiClient.get("/me");
  return response.data;
}

export async function getAdminDashboard() {
  const response = await apiClient.get("/admin/dashboard");
  return response.data;
}

export async function getCompanyDashboard() {
  const response = await apiClient.get("/company/dashboard");
  return response.data;
}

/**
 * Fetch student dashboard data (Stage 6.1).
 * GET /student/dashboard — requires Student JWT
 */
export async function getStudentDashboard() {
  const response = await apiClient.get("/student/dashboard");
  return response.data;
}

/**
 * Fetch student profile (Stage 6.2).
 * GET /student/profile
 */
export async function getStudentProfile() {
  const response = await apiClient.get("/student/profile");
  return response.data;
}

/**
 * Update student profile (Stage 6.2).
 * PUT /student/profile
 * Body: { full_name, phone, cgpa, skills }
 */
export async function updateStudentProfile(profileData) {
  const response = await apiClient.put("/student/profile", profileData);
  return response.data;
}

/**
 * Upload student resume PDF (Stage 6.2).
 * POST /student/upload-resume — multipart/form-data with field "resume"
 */
export async function uploadStudentResume(file) {
  const formData = new FormData();
  formData.append("resume", file);

  // Axios detects FormData and sets multipart/form-data with boundary
  const response = await apiClient.post("/student/upload-resume", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/**
 * Browse ONLY approved placement drives (Stage 7.2).
 *
 * GET /student/drives
 * Optional query params:
 *   - job_title
 *   - company_name
 *   - branch
 *   - year
 *   - minimum_cgpa
 */
export async function getApprovedDrives(params = {}) {
  const response = await apiClient.get("/student/drives", { params });
  return response.data;
}

/**
 * Apply to a placement drive (Stage 7 Combined).
 * POST /student/apply/<drive_id>
 */
export async function applyToDrive(driveId) {
  const response = await apiClient.post(`/student/apply/${driveId}`);
  return response.data;
}

/**
 * Fetch logged-in student's applications (Stage 7 Combined).
 * GET /student/applications
 */
export async function getMyApplications() {
  const response = await apiClient.get("/student/applications");
  return response.data;
}

export async function getCompanyDrives() {
  const response = await apiClient.get("/company/drives");
  return response.data;
}

export async function createPlacementDrive(driveData) {
  const response = await apiClient.post("/company/drives", driveData);
  return response.data;
}

/**
 * Update an existing placement drive (Stage 5.3).
 * PUT /company/drives/<id>
 */
export async function updatePlacementDrive(driveId, driveData) {
  const response = await apiClient.put(`/company/drives/${driveId}`, driveData);
  return response.data;
}

/**
 * Close a placement drive (Stage 5.3).
 * PATCH /company/drives/<id>/close
 */
export async function closePlacementDrive(driveId) {
  const response = await apiClient.patch(`/company/drives/${driveId}/close`);
  return response.data;
}

// ---------- Admin approval APIs (Stage 4.2) ----------

export async function fetchCompanies() {
  const response = await apiClient.get("/admin/companies");
  return response.data;
}

export async function approveCompany(companyId) {
  const response = await apiClient.put(`/admin/company/${companyId}/approve`);
  return response.data;
}

export async function rejectCompany(companyId) {
  const response = await apiClient.put(`/admin/company/${companyId}/reject`);
  return response.data;
}

export async function fetchDrives() {
  const response = await apiClient.get("/admin/drives");
  return response.data;
}

export async function approveDrive(driveId) {
  const response = await apiClient.put(`/admin/drive/${driveId}/approve`);
  return response.data;
}

export async function rejectDrive(driveId) {
  const response = await apiClient.put(`/admin/drive/${driveId}/reject`);
  return response.data;
}

export default apiClient;
