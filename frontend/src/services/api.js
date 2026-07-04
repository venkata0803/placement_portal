/**
 * services/api.js - API Service
 *
 * This file handles all HTTP requests to the Flask backend.
 * We use Axios to send GET, POST, PUT, DELETE requests.
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
 * Check if the backend is running.
 * Calls GET / on the Flask server.
 *
 * @returns {Promise} Response data with { message: "..." }
 */
export async function checkBackendStatus() {
  const response = await apiClient.get("/");
  return response.data;
}
