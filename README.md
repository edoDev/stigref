# stigref

**Fast, static STIG & control reference.** Search DISA STIGs/SRGs and related NIST controls in the browser. No account, no backend, no assessment workflow.

> Status: **Live** — shareable search/filters, copy packs, Intune coverage, CVE/KEV threat panel.  
> Site: https://edodev.github.io/stigref/

## Why this exists

| Product | What it is |
|---------|------------|
| [STIG Manager](https://github.com/NUWCDIVNPT/stig-manager) | Full assessment platform (assets, collections, reviews, OIDC, MySQL) |
| Official [STIG Viewer](https://public.cyber.mil/stigs/srg-stig-tools/) | Desktop XCCDF viewer from DISA |
| **stigref** | Lightweight **reference + search + shareable links + copy/paste** on GitHub Pages |

stigref does **not** track compliance, assets, or .ckl workflows. It answers: *“What does this STIG rule say, and how do I link or paste it cleanly?”*

## Goals (v1)

1. **Fast, lightweight frontend** — snappy search, minimal JS, works on modest hardware.
2. **Robust search** — STIG titles, rule IDs, rule titles, check/fix text (indexed), control IDs.
3. **Deep links** — stable URLs for STIGs, rules, and controls (shareable in tickets/chat).
4. **Clean copy & paste** — one-click copy of rule ID, title, check, fix, or a compact citation block.
5. **Free hosting** — static site on GitHub Pages.
6. **Quarterly content refresh** — download public `U_` DISA library ZIP → local (or CI) build script → commit/publish data + show **Content last updated**.

## Non-goals (v1)

- Assessment status, assets, collections, POA&M
- Auth, multi-user, or API server
- CUI / CAC-only STIGs
- Replacing STIG Manager or eMASS

## Architecture (summary)

```
DISA U_ SRG-STIG Library ZIP  ──►  scripts/build   ──►  data/*.json
                                                      │
GitHub Pages  ◄──  Vite SPA (web/)  ◄── fetch ────────┘
```

- **Data:** compact search index + lazy-loaded detail JSON.
- **UI:** modern SPA (Vite + TypeScript; React or Svelte — finalize at build start).
- **Search:** MiniSearch (or equivalent) in a Web Worker.
- **Hosting:** GitHub Pages only.

Details: [docs/DESIGN.md](docs/DESIGN.md) · [Backlog](docs/BACKLOG.md) · [Roadmap](docs/ROADMAP.md)

## Content source

Public unclassified packages from DoD Cyber Exchange / `dl.dod.cyber.mil` (e.g. `U_SRG-STIG_Library_*.zip`).  
CUI packages are out of scope.

## Repo layout (planned)

```
stigref/
├── docs/           # design, architecture, review prompts
├── scripts/        # ZIP → data pipeline (Python)
├── web/            # frontend SPA
├── data/           # generated static JSON (published; large)
├── raw/            # local ZIP only (gitignored)
└── .github/        # Pages deploy workflow
```

## License

MIT (code). STIG content remains subject to DISA / U.S. Government distribution terms for public `U_` materials. This project redistributes **derived, transformed** public content for reference convenience—operators must not include CUI.

## Credits

Inspired by the product idea behind [rmfdb](https://github.com/atomweight/rmfdb) (static rethink). Differentiated from [STIG Manager](https://github.com/NUWCDIVNPT/stig-manager) (assessment vs reference).

## Quick start (data pipeline)

```powershell
cd scripts
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
python -m stigref_build --input testdata\sample_stig-xccdf.xml --out ..\data
```

See [scripts/README.md](scripts/README.md).

## Status

| Phase | State |
|-------|--------|
| Design | Done |
| Phase 1 — parser + data build | **Done** |
| Phase 2 — frontend UI | **Done** (Svelte + MiniSearch) |
| Full DISA library ingest | **Done** (committed in `data/`) |
| GitHub Pages live | Enable Actions source in repo Settings → Pages |

## Web UI

```powershell
cd web
npm install
npm run dev
# open http://localhost:5173/stigref/
```

Production build: `npm run build` (copies `data/` into `dist/data`).
