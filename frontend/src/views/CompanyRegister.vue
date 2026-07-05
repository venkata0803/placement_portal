<script setup>
/**
 * CompanyRegister.vue - Company Registration Page
 *
 * Collects company details and sends them to POST /register/company.
 * Company approval_status is set to "Pending" on the backend.
 */

import { ref } from "vue";
import { useRouter } from "vue-router";
import { registerCompany } from "../services/api.js";

const router = useRouter();

// Form fields
const form = ref({
  username: "",
  email: "",
  password: "",
  company_name: "",
  website: "",
  hr_name: "",
  hr_email: "",
  description: "",
});

const errorMessage = ref("");
const successMessage = ref("");
const isLoading = ref(false);

async function handleRegister() {
  errorMessage.value = "";
  successMessage.value = "";

  // Frontend validation: required fields
  const requiredFields = [
    "username",
    "email",
    "password",
    "company_name",
    "hr_name",
    "hr_email",
  ];

  for (const field of requiredFields) {
    if (!form.value[field]?.trim()) {
      errorMessage.value = `${field.replace("_", " ")} is required`;
      return;
    }
  }

  isLoading.value = true;

  try {
    // Call POST /register/company API
    const response = await registerCompany(form.value);

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
            <h2 class="card-title text-center mb-4">Company Registration</h2>

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
                <label class="form-label">Company Name</label>
                <input
                  v-model="form.company_name"
                  type="text"
                  class="form-control"
                  required
                />
              </div>

              <div class="mb-3">
                <label class="form-label">Website (optional)</label>
                <input
                  v-model="form.website"
                  type="url"
                  class="form-control"
                  placeholder="https://example.com"
                />
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">HR Name</label>
                  <input
                    v-model="form.hr_name"
                    type="text"
                    class="form-control"
                    required
                  />
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">HR Email</label>
                  <input
                    v-model="form.hr_email"
                    type="email"
                    class="form-control"
                    required
                  />
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">Description (optional)</label>
                <textarea
                  v-model="form.description"
                  class="form-control"
                  rows="3"
                ></textarea>
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="isLoading"
              >
                {{ isLoading ? "Registering..." : "Register as Company" }}
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
