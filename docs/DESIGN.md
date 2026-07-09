# stigref — Product & Technical Design

**Version:** 0.1 (pre-implementation)  
**Audience:** Maintainers + external design review  
**Status:** Phase 1 implemented (build pipeline + sample data)

---

## 1. Problem

Security engineers constantly need to:

- Find a STIG rule or NIST control quickly
- Open a **stable link** in a ticket, PR, or chat
- **Copy** check/fix/title text without fighting desktop viewers or multi-hundred-MB ZIPs

Existing options:

| Option | Gap for this use case |
|--------|------------------------|
| DISA STIG Viewer | Desktop; weak shareable web links; not search-first for the whole library |
| cyber.mil downloads | ZIP distribution only; no browsable corpus for a free static site |
| STIG Manager | Correct tool for **assessment** (assets, reviews, OIDC, DB)—heavy for “look up a rule” |
| rmfdb (original) | SPA + dead API; spinner-on-error; not static-hostable |

**stigref** is a **static reference browser**: search → open → copy → share link.

---

## 2. Product principles

1. **Reference, not assessment** — no status, no assets, no login.
2. **Speed over completeness of chrome** — few routes, aggressive data splitting.
3. **Links are first-class** — every entity has a canonical URL.
4. **Copy is first-class** — one click, plain text, predictable format.
5. **Honest loading states** — loading / empty / error; never infinite spinner.
6. **Public content only** — `U_` library; document last update from build metadata.
7. **Build offline, serve static** — GitHub Pages; no runtime dependency on DISA CDN (CORS + size).

---

## 3. Differentiation: STIG Manager vs stigref

```
STIG Manager                          stigref
─────────────────────────────         ─────────────────────────────
Track compliance on assets            Look up what a rule says
Collections, reviews, metrics         Search, detail, copy, link
MySQL + OIDC + API                    Static JSON + SPA
Deploy as platform                    Host on GitHub Pages free
Operators / ISSOs / assessors         Anyone needing a quick reference
```

They are **complementary**. stigref can link *out*; it does not replace STIG Manager.

---

## 4. User stories (v1)

1. As a user, I type a rule ID or keyword and see ranked hits in &lt;100ms after index load.
2. As a user, I open `/rules/SV-…` (or chosen ID scheme) and see title, severity, check, fix, STIG membership, CCI/control links.
3. As a user, I open `/stigs/{id}` and see metadata + rule list.
4. As a user, I open `/controls/{id}` and see control text + linked CCIs/rules when mapped.
5. As a user, I click **Copy** on a block and get clean plain text (no HTML junk).
6. As a user, I see **Content last updated** from `meta.json` in the chrome.
7. As a maintainer, I download one DISA library ZIP, run one script, push, and Pages updates.

---

## 5. Information architecture & URLs

Stable, readable paths (GitHub project Pages: prefix with `/stigref/` via Vite `base`):

| Route | Purpose |
|-------|---------|
| `/` | Search-first home; recent / featured STIG list from index |
| `/search?q=` | Explicit search results (optional; may merge with `/`) |
| `/stigs` | Paginated STIG catalog |
| `/stigs/:stigId` | STIG detail + rules table |
| `/rules/:ruleId` | Rule detail (canonical share target) |
| `/controls` | Control catalog (if fixtures shipped in v1) |
| `/controls/:controlId` | Control detail |
| `/ccis/:cciId` | CCI detail (v1.1 if not in v1) |
| `/about` | Source, update process, license, limitations |

**ID rules (proposal):**

- **Rule:** DISA `full_rule_id` or group+rule form as published (URL-encoded as needed). Prefer the identifier people already paste (`SV-…` / `V-…` patterns as present in XCCDF).
- **STIG:** Deterministic slug or hash of `name|version|release` so rebuilds stay stable across pipeline runs.
- **Control:** NIST id (`AC-2`, `AC-2(1)`, …).

Query params for UX only (highlight, tab)—not required for identity.

---

## 6. Copy & paste design

Every primary entity page exposes:

| Action | Clipboard content (example) |
|--------|-----------------------------|
| Copy rule ID | `SV-230221r627750_rule` |
| Copy title | Rule title only |
| Copy check | Check content plain text |
| Copy fix | Fix text plain text |
| Copy citation | Multi-line block (see below) |

**Citation block (v1 default):**

```text
Rule: SV-230221r627750_rule
Title: …
Severity: medium
STIG: Red Hat Enterprise Linux 8 STIG · V2R3
Link: https://<user>.github.io/stigref/rules/SV-230221r627750_rule
```

Optional later: Markdown citation for GitHub issues.

UX: visible buttons, keyboard-friendly, toast “Copied”. Never rely on selecting text in a card.

---

## 7. Data architecture

### 7.1 Pipeline

```
raw/U_SRG-STIG_Library_*.zip   (gitignored)
        │
        ▼
scripts/build_data.py
  • unzip nested *_STIG.zip / *_SRG.zip
  • parse XCCDF 1.1 (defusedxml)
  • optional: NIST 800-53 + CCI fixtures
  • write data/ + meta.json
        │
        ▼
data/
  meta.json
  stigs/index.json
  stigs/by-id/{stigId}.json
  rules/by-id/{ruleId}.json      # or rules embedded only in STIG + separate thin rule files for deep links
  controls/index.json
  controls/by-id/{id}.json
  search/documents.json          # compact MiniSearch corpus (or shards)
```

### 7.2 `meta.json`

```json
{
  "lastUpdated": "2026-04-07T00:00:00Z",
  "source": {
    "filename": "U_SRG-STIG_Library_April_2026.zip",
    "sha256": "…",
    "urlHint": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/"
  },
  "counts": { "stigs": 0, "rules": 0, "controls": 0 },
  "generator": "stigref-build 0.1.0"
}
```

### 7.3 Search documents (compact)

Index fields only—full check/fix live in detail JSON:

- `id`, `type` (`stig`|`rule`|`control`|`cci`)
- `title`, `body` (truncated searchable text)
- `route`, severity, stigName (for rules)

Shard by type if `documents.json` exceeds ~10–15 MB gzipped budget.

### 7.4 Why not fetch DISA from the browser?

- No CORS on `dl.dod.cyber.mil` for SPA origins
- Library ~350MB+; nested ZIP + XCCDF unsuitable for client-only product
- Pages must own transformed artifacts

Optional later: CI job discovers latest `U_SRG-STIG_Library_*.zip` from the public directory index and builds—still a build, not live proxying.

---

## 8. Frontend architecture

### 8.1 Stack (recommended)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Build | Vite | Fast, Pages-friendly |
| Language | TypeScript | Safer data contracts |
| UI | React or Svelte | Pick one at kickoff; prefer **Svelte** if pure simplicity, **React** if contributor familiarity |
| Router | Official router with path mode + Pages `404.html` fallback | Deep links |
| Search | MiniSearch in Web Worker | Non-blocking UI |
| Styling | Minimal CSS (or Pico / open props)—not a heavy component mega-kit | Lightweight |

### 8.2 Performance budgets (targets)

| Metric | Target |
|--------|--------|
| Initial JS (gzip) | &lt; 150 KB app + framework |
| Search index first load | Progressive; usable within a few seconds on broadband |
| Query latency after load | &lt; 50–100 ms typical |
| Detail navigation | Fetch one small JSON; no full-corpus reload |

### 8.3 Error handling (mandatory)

- Every async path: `idle | loading | success | error`
- Failed `meta.json` → banner “data not deployed”
- Failed detail → “not found” with search CTA
- No `else loading` without timeout/error branch (lesson from rmfdb)

---

## 9. Build & deploy

1. Maintainer (or CI): produce `data/`
2. `web` build copies/serves `data/` into `dist/`
3. GitHub Actions → GitHub Pages
4. `base` path set for project site (`/stigref/`)

**Git strategy:**

- Prefer committing generated `data/` if size stays reasonable (many medium files).
- If too large: Release assets + Actions merge at deploy (fallback).

---

## 10. Phased delivery

### Phase 0 — Approval (this document)

- Name, scope, stack preference confirmation

### Phase 1 — Pipeline MVP

- Parse one STIG ZIP end-to-end
- Emit `meta.json`, STIG index, one detail shape
- Golden tests on sample XCCDF

### Phase 2 — UI MVP

- Home search (titles + rule IDs first)
- STIG + rule detail with copy buttons
- Deep links work on Pages

### Phase 3 — Full library + polish

- Full `U_` library ingest
- Search body fields / shards / worker
- Control fixtures + links
- About page, last updated chrome

### Phase 4 — Hardening

- CI deploy, size budgets, README “how to update quarterly”
- Optional: scheduled CI discover latest library name

---

## 11. Risks

| Risk | Mitigation |
|------|------------|
| Data size | Split files; compact index; measure early with full library |
| XCCDF variance | Defensive parser; skip+log; fixtures for known edge cases |
| ID instability | Deterministic IDs from XCCDF fields; document scheme |
| DISA mid-quarter releases | README: library is quarterly; individual ZIP optional later |
| Scope creep into STIG Manager | Explicit non-goals; reject assessment features in v1 |

---

## 12. Success criteria

- [ ] Works on GitHub Pages with no backend
- [ ] Search finds rules by ID and keyword after index load
- [ ] Deep link to rule opens correct page on refresh
- [ ] Copy citation produces clean plain text
- [ ] `meta.json` drives visible last-updated date
- [ ] Full public library build documented in &lt;30 minutes maintainer time (excluding download)

---

## 13. Open decisions for owner

1. **UI framework:** Svelte vs React (default recommendation: **Svelte + Vite** for smallest surface).
2. **v1 controls:** include NIST 800-53 fixtures day one, or STIGs/rules only first?
3. **GitHub visibility:** public vs private during build.
4. **Repo owner:** personal user vs org.
5. **Domain:** default `*.github.io/stigref` vs custom later.

---

## 14. Name

**stigref** — *STIG Reference*

- Short, typeable, available as a conceptual product name
- Signals “reference” not “manager/assessment”
- npm/github collision risk: check at creation time; alt names: `stigfind`, `stigdex`, `openstigref`
