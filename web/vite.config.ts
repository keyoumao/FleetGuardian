import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "localhost", port: 5173, strictPort: true, open: true,
    proxy: { "/api/monitor": { target: "http://127.0.0.1:8766", changeOrigin: true }, "/api/source-": { target: "http://127.0.0.1:8765", changeOrigin: true } },
  },
});
