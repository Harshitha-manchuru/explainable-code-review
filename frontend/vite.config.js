import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// index.html lives in public/ per the required project structure, but
// Vite's dev server expects its entry HTML at the configured root. We
// point root at public/ and use an absolute filesystem alias so the
// "/src/main.jsx" script reference in index.html resolves correctly
// regardless of root.
export default defineConfig({
  plugins: [react()],
  root: "public",
  publicDir: false,
  resolve: {
    alias: {
      "/src": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
  },
});
