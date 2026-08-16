import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: (() => {
      const target =
        process.env.VITE_DEV_PROXY_TARGET ?? "http://localhost:8000";
      return {
        "/api": {
          target,
          changeOrigin: true,
        },
      };
    })(),
  },
});
