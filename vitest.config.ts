import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["desktop/src/**/*.test.ts", "shared/**/*.test.ts"],
    environment: "node",
  },
  resolve: {
    alias: {
      "@": new URL("./desktop/src", import.meta.url).pathname,
      "@shared": new URL("./shared", import.meta.url).pathname,
    },
  },
});
