import { defineConfig } from "vitest/config";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte({ hot: false })],
  base: "/stigref/",
  test: {
    environment: "happy-dom",
    include: ["src/**/*.{test,spec}.ts"],
    globals: false,
  },
});
