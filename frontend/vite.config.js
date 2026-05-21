import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  define: {
    global: "globalThis",
  },
  build: {
    rollupOptions: {
      external: (id) => id.startsWith("node:"),
    },
  },
  optimizeDeps: {
    esbuildOptions: {
      define: { global: "globalThis" },
    },
  },
});