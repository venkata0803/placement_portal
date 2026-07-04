/**
 * main.js - Frontend Entry Point
 *
 * This file bootstraps the Vue application:
 * 1. Imports Bootstrap CSS for styling
 * 2. Creates the Vue app
 * 3. Registers Vue Router
 * 4. Mounts the app to the HTML element #app
 */

import { createApp } from "vue";
import App from "./App.vue";
import router from "./router/index.js";

// Import Bootstrap CSS (JavaScript bundle is optional for basic styling)
import "bootstrap/dist/css/bootstrap.min.css";

// Create the Vue application
const app = createApp(App);

// Tell Vue to use the router for page navigation
app.use(router);

// Mount the app to the div with id="app" in index.html
app.mount("#app");
