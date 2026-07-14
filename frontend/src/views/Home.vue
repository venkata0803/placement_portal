<script setup>
/**
 * Home.vue - Landing page of the Placement Portal Application
 *
 * Displays a professional project introduction and technology stack overview.
 */
</script>

<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-12 col-md-10 col-lg-8">
        <div class="card shadow-sm border-0">
          <div class="card-body p-4 p-md-5">
            <h1 class="card-title text-center mb-4 fs-2">
              Placement Portal Application
            </h1>

            <p class="card-text text-secondary lh-lg mb-4">
              The Placement Portal Application is a web-based platform that
              streamlines campus recruitment by connecting students, companies,
              and the institute placement cell. It enables company registration
              and approval, placement drive management, student applications,
              interview scheduling, and application tracking through a secure
              role-based system. The application also includes Redis caching,
              Celery background jobs, CSV exports, and automated email
              notifications to improve performance and user experience.
            </p>

            <div class="bg-light rounded p-3 p-md-4 mt-2">
              <h2 class="h6 text-uppercase text-muted mb-3">Built With</h2>
              <ul class="list-unstyled mb-0 row g-2">
                <li class="col-12 col-sm-6">
                  <span class="text-primary me-1">•</span> Flask REST API
                </li>
                <li class="col-12 col-sm-6">
                  <span class="text-primary me-1">•</span> Vue.js
                </li>
                <li class="col-12 col-sm-6">
                  <span class="text-primary me-1">•</span> SQLite
                </li>
                <li class="col-12 col-sm-6">
                  <span class="text-primary me-1">•</span> Redis Cache
                </li>
                <li class="col-12 col-sm-6">
                  <span class="text-primary me-1">•</span> Celery
                </li>
                <li class="col-12 col-sm-6">
                  <span class="text-primary me-1">•</span> JWT Authentication
                </li>
                <li class="col-12 col-sm-6">
                  <span class="text-primary me-1">•</span> Bootstrap 5
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
