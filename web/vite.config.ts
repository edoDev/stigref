import { defineConfig, type Plugin } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import fs from "node:fs";
import path from "node:path";
import type { IncomingMessage, ServerResponse } from "node:http";

const repoData = path.resolve(__dirname, "../data");

/** Serve ../data at /data (and under base) during dev. */
function serveDataPlugin(): Plugin {
  const handler = (
    req: IncomingMessage,
    res: ServerResponse,
    next: () => void,
  ) => {
    const raw = req.url || "";
    const urlPath = raw.split("?")[0] || "";
    // With base /stigref/, requests may be /stigref/data/... or /data/...
    const markers = ["/data/", "/data"];
    let rel: string | null = null;
    for (const m of markers) {
      const idx = urlPath.indexOf(m);
      if (idx !== -1) {
        rel = urlPath.slice(idx + "/data".length);
        break;
      }
    }
    if (rel === null) return next();
    if (rel === "" || rel === "/") rel = "/meta.json"; // shouldn't happen
    const safe = path.normalize(rel).replace(/^(\.\.(\/|\\|$))+/, "");
    const filePath = path.join(repoData, safe);
    if (!filePath.startsWith(repoData)) {
      res.statusCode = 403;
      res.end("Forbidden");
      return;
    }
    fs.stat(filePath, (err, st) => {
      if (err || !st.isFile()) {
        res.statusCode = 404;
        res.end("Not found");
        return;
      }
      res.setHeader("Content-Type", "application/json; charset=utf-8");
      res.setHeader("Cache-Control", "no-cache");
      fs.createReadStream(filePath).pipe(res);
    });
  };

  return {
    name: "stigref-serve-data",
    configureServer(server) {
      server.middlewares.use(handler);
    },
    configurePreviewServer(server) {
      server.middlewares.use(handler);
    },
  };
}

// Project Pages: https://edoDev.github.io/stigref/
export default defineConfig({
  base: "/stigref/",
  plugins: [svelte(), serveDataPlugin()],
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    // Do not ship source maps to GitHub Pages (saves ~0.7 MB, less source exposure).
    sourcemap: false,
  },
});
