import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// В dev-режиме фронт работает на :5173, а API/файлы на :8000.
// Прокидываем относительные пути на бэкенд, чтобы куки сессии
// работали из коробки (один origin для браузера).
const BACKEND = process.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api": { target: BACKEND, changeOrigin: false },
      "/uploads": { target: BACKEND, changeOrigin: false },
      "/receipts": { target: BACKEND, changeOrigin: false },
      "/healthz": { target: BACKEND, changeOrigin: false },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    chunkSizeWarningLimit: 1500,
  },
});
