import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, externalizeDepsPlugin } from "electron-vite";

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: resolve(__dirname, "desktop/electron/main.ts"),
        output: { entryFileNames: "main.js" },
      },
    },
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: resolve(__dirname, "desktop/electron/preload.ts"),
        output: { entryFileNames: "preload.cjs", format: "cjs" },
      },
    },
  },
  renderer: {
    root: resolve(__dirname, "desktop"),
    plugins: [react()],
    resolve: {
      alias: {
        "@": resolve(__dirname, "desktop/src"),
        "@shared": resolve(__dirname, "shared"),
      },
    },
    build: {
      rollupOptions: {
        input: resolve(__dirname, "desktop/index.html"),
      },
    },
  },
});
