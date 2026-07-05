<script setup>
/**
 * StudentRegister.vue - Student Registration Page
 *
 * Collects student details and sends them to POST /register/student.
 */

import { ref } from "vue";
import { useRouter } from "vue-router";
import { registerStudent } from "../services/api.js";

const router = useRouter();

// Form fields
const form = ref({
  username: "",
  email: "",
  password: "",
  full_name: "",
  branch: "",
  year: "",
  cgpa: "",
  phone: "",
});

const errorMessage = ref("");
const successMessage = ref("");
const isLoading = ref(false);

async function handleRegister() {
  errorMessage.value = "";
  successMessage.value = "";

  // Frontend validation: all fields required
  for (const [field, value] of Object.entries(form.value)) {
    if (value === "" || value === null) {
      errorMessage.value = `${field.replace("_", " ")} is required`;
      return;
    }
  }

  isLoading.value = true;

  try {
    // Call POST /register/student API
    const response = await registerStudent({
      ...form.value,
      year: Number(form.value.year),
      cgpa: Number(form.value.cgpa),
    });

    successMessage.value = response.message;

    // Redirect to login after short delay
    setTimeout(() => {
      router.push("/login");
    }, 1500);
  } catch (error) {
    errorMessage.value =
      error.response?.data?.message || "Registration failed. Please try again.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-8 col-lg-7">
        <div class="card shadow">
          <div class="card-body">
            <h2 class="card-title text-center mb-4">Student Registration</h2>

            <div v-if="errorMessage" class="alert alert-danger">
              {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="alert alert-success">
              {{ successMessage }}
            </div>

            <form @submit.prevent="handleRegister">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">Username</label>
                  <input
                    v-model="form.username"
                    type="text"
                    class="form-control"
                    required
                  />
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">Email</label>
                  <input
                    v-model="form.email"
                    type="email"
                    class="form-control"
                    required
                  />
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Password</label>
                <input
                  v-model="form.password"
                  type="password"
                  class="form-control"
                  required
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Full Name</label>
                <input
                  v-model="form.full_name"
                  type="text"
                  class="form-control"
                  required
                />
              </div>

              <div class="row">
                <div class="col-md-4 mb-3">
                  <label class="form-label">Branch</label>
                  <input
                    v-model="form.branch"
                    type="text"
                    class="form-control"
                    placeholder="e.g. CSE"
                    required
                  />
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">Year</label>
                  <input
                    v-model="form.year"
                    type="number"
                    class="form-control"
                    min="1"
                    max="4"
                    required
                  />
                </div>
                <div class="col-md-4 mb-3">
                  <label class="form-label">CGPA</label>
                  <input
                    v-model="form.cgpa"
                    type="number"
                    step="0.01"
                    class="form-control"
                    min="0"
                    max="10"
                    required
                  />
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Phone</label>
                <input
                  v-model="form.phone"
                  type="tel"
                  class="form-control"
                  required
                />
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="isLoading"
              >
                {{ isLoading ? "Registering..." : "Register as Student" }}
              </button>
            </form>

            <p class="text-center mt-3 mb-0">
              Already have an account?
              <router-link to="/login">Login here</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
