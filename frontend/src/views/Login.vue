<script setup>
/**
 * Login.vue - Login Page
 *
 * User enters email and password.
 * On success: store JWT in localStorage and redirect by role.
 */

import { ref } from "vue";
import { useRouter } from "vue-router";
import { login, saveAuthData } from "../services/api.js";

const router = useRouter();

// Form fields
const email = ref("");
const password = ref("");

// UI messages
const errorMessage = ref("");
const successMessage = ref("");
const isLoading = ref(false);

// Map role to dashboard route
const roleRoutes = {
  admin: "/admin",
  student: "/student",
  company: "/company",
};

async function handleLogin() {
  errorMessage.value = "";
  successMessage.value = "";

  // Frontend validation: required fields
  if (!email.value.trim() || !password.value) {
    errorMessage.value = "Email and password are required";
    return;
  }

  isLoading.value = true;

  try {
    // Call POST /login API
    const response = await login(email.value.trim(), password.value);

    // Save JWT token, role, and username in localStorage
    saveAuthData(response.token, response.role, response.username);

    successMessage.value = "Login successful! Redirecting...";

    // Redirect user based on their role
    const redirectPath = roleRoutes[response.role] || "/";
    router.push(redirectPath);
  } catch (error) {
    errorMessage.value =
      error.response?.data?.message || "Login failed. Please try again.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow">
          <div class="card-body">
            <h2 class="card-title text-center mb-4">Login</h2>

            <!-- Error message -->
            <div v-if="errorMessage" class="alert alert-danger">
              {{ errorMessage }}
            </div>

            <!-- Success message -->
            <div v-if="successMessage" class="alert alert-success">
              {{ successMessage }}
            </div>

            <form @submit.prevent="handleLogin">
              <!-- Email -->
              <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input
                  id="email"
                  v-model="email"
                  type="email"
                  class="form-control"
                  required
                />
              </div>

              <!-- Password -->
              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input
                  id="password"
                  v-model="password"
                  type="password"
                  class="form-control"
                  required
                />
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="isLoading"
              >
                {{ isLoading ? "Logging in..." : "Login" }}
              </button>
            </form>

            <p class="text-center mt-3 mb-0">
              New student?
              <router-link to="/register/student">Register here</router-link>
            </p>
            <p class="text-center mt-2">
              New company?
              <router-link to="/register/company">Register here</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
