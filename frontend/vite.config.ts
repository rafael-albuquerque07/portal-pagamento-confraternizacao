import { defineConfig } from "vite";

export default defineConfig({
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/webhooks": "http://localhost:8000",
    },
  },
});
