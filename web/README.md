# stigref web

Svelte + Vite static UI for the `data/` catalog.

## Develop

```powershell
cd web
npm install
npm run dev
```

Open http://localhost:5173/stigref/ (base path matches GitHub Pages).

The dev server serves `../data` at `/stigref/data/…`.

## Build

```powershell
npm run build
npm run preview
```

`build` copies `../data` into `dist/data` and writes `404.html` for SPA fallback.
