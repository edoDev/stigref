/* stigref offline shell (B-042) — caches app shell only, not full data tree */
const CACHE = "stigref-shell-v1";
const SHELL = ["./", "./index.html", "./404.html"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL).catch(() => undefined)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  // Network-first for data JSON; cache-first for shell assets
  if (url.pathname.includes("/data/")) {
    event.respondWith(
      fetch(req)
        .then((res) => res)
        .catch(() => caches.match(req)),
    );
    return;
  }
  event.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      const copy = res.clone();
      if (res.ok && (url.pathname.endsWith(".js") || url.pathname.endsWith(".css") || url.pathname.endsWith(".html"))) {
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    })),
  );
});
