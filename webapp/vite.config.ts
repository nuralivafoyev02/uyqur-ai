import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      components: path.resolve(__dirname, "./src/components"),
      hooks: path.resolve(__dirname, "./src/hooks"),
      layouts: path.resolve(__dirname, "./src/layouts"),
      lib: path.resolve(__dirname, "./src/lib"),
      pages: path.resolve(__dirname, "./src/pages"),
      types: path.resolve(__dirname, "./src/types")
    }
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": "http://localhost:8788",
      "/health": "http://localhost:8788",
      "/telegram": "http://localhost:8788"
    }
  }
});
