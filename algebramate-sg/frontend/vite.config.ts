import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/auth": "http://127.0.0.1:8000",
      "/topics": "http://127.0.0.1:8000",
      "/diagnostic": "http://127.0.0.1:8000",
      "/practice": "http://127.0.0.1:8000",
      "/progress": "http://127.0.0.1:8000",
    },
  },
});
