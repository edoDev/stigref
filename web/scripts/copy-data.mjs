/**
 * Copy repo data/ into dist/data after vite build (GitHub Pages static assets).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const src = path.resolve(__dirname, "../../data");
const dest = path.resolve(__dirname, "../dist/data");

if (!fs.existsSync(src)) {
  console.error("data/ not found at", src);
  process.exit(1);
}

fs.mkdirSync(path.dirname(dest), { recursive: true });
fs.cpSync(src, dest, { recursive: true });
console.log("Copied data/ → dist/data");

// SPA fallback for GitHub Pages path reloads
const index = path.resolve(__dirname, "../dist/index.html");
const fallback = path.resolve(__dirname, "../dist/404.html");
if (fs.existsSync(index)) {
  fs.copyFileSync(index, fallback);
  console.log("Wrote dist/404.html for SPA fallback");
}
