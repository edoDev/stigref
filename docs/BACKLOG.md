# stigref product backlog

**Last updated:** 2026-07-10  
**Status:** Living document  
**Product:** [stigref](https://github.com/edoDev/stigref) — static STIG reference (search, deep links, copy, Intune CSP hints)

**July 2026 review:** [REVIEW_2026-07.md](REVIEW_2026-07.md) — ops/hygiene follow-ups B-071–B-076.  
**Session resume:** [SESSION_LOG.md](SESSION_LOG.md)

---

## How to use this backlog

| Field | Meaning |
|--------|---------|
| **ID** | Stable backlog id (`B-xxx`) |
| **Priority** | P0 now → P3 later / nice-to-have |
| **Size** | S / M / L / XL (rough engineering effort) |
| **Depends** | Other backlog ids |
| **Status** | `idea` · `planned` · `in progress` · `done` · `wontfix` |

**Non-goals (keep product sharp):** full assessment platform (STIG Manager), CUI content, live cyber.mil at browse time, presenting unvetted threat intel as authoritative without labels.

---

## Epic index

| Epic | Theme |
|------|--------|
| **E1** | Daily UX (search, share, copy, keyboard) |
| **E2** | Intune / CSP |
| **E3** | Version history & change management |
| **E4** | Discovery & navigation |
| **E5** | Trust & light workflow |
| **E6** | Performance & polish |
| **E7** | Content breadth |
| **E8** | Collaboration & distribution |
| **E9** | Threat intel enrichment (CVE / KEV / ATT&CK / PoC / IoC / reports) |

---

## Full backlog

### E1 — Daily UX

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-001 | Saved searches / bookmarks (localStorage) | P0 | M | done | No account |
| B-002 | Shareable search URLs (`?q=&vendor=&…`) | P0 | S | done | Deep-link results |
| B-003 | Rule comparison (two rules / revisions) | P1 | L | idea | |
| B-004 | Related rules (group / CCI / registry / CSP) | P1 | M | planned | |
| B-005 | Copy packs (markdown, citation, OMA-URI, check+fix) | P0 | S | done | |
| B-006 | Keyboard-first UX | P1 | M | planned | |
| B-007 | Print / PDF-friendly rule view | P2 | S | idea | |
| B-008 | Severity / CCI filters on search | P0 | M | done | Facets + URL |
| B-009 | “Open in Intune” guidance recipes | P1 | M | done | With export |
| B-010 | Intune coverage meter per product | P0 | S | done | Quick links |

### E2 — Intune / CSP

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-011 | Expand curated maps (Server / Defender / Edge) | P0 | L | planned | Ongoing |
| B-012 | All Microsoft Windows STIGs (not only quick-links) | P1 | L | planned | Was “1B backlog” |
| B-013 | Settings Catalog names beside OMA-URI | P1 | M | idea | |
| B-014 | Multi-option ranking (preferred native vs ADMX) | P1 | M | planned | |
| B-015 | Conflict warnings (same CSP/registry, different values) | P2 | M | idea | |
| B-016 | Intune baseline pack export (JSON + CSV + readme) | P0 | M | done | Extends product JSON |
| B-017 | Map contribution helper (YAML snippet generator) | P2 | M | idea | |
| B-018 | CSP catalog refresh job (quarterly with library) | P1 | L | planned | |
| B-019 | Chrome / Office ADMX path documentation + maps | P2 | L | idea | |
| B-020 | “Verify in Windows” PowerShell hints | P2 | M | idea | |

### E3 — Version history

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-021 | Multi-release storage (`data/releases/…`) | P0 | L | planned | See VERSION_HISTORY.md |
| B-022 | Quarterly “what changed” report | P0 | L | planned | |
| B-023 | Per-family previous version links | P1 | M | planned | |
| B-024 | Static changelog / release notes page | P1 | S | planned | |
| B-025 | Watchlist “changed since last release” | P3 | L | idea | Local list |

### E4 — Discovery

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-026 | Faceted search (type, vendor, role, severity, has-Intune, has-CVE…) | P0 | M | done | Overlaps B-008 |
| B-027 | CCI browser (CCI → rules → STIGs) | P1 | L | planned | |
| B-028 | NIST 800-53 control pages | P2 | L | idea | Fixtures |
| B-029 | Product hubs (`/products/windows-11`) | P0 | M | done | |
| B-030 | Recently viewed | P1 | S | planned | |
| B-031 | Typo-tolerant rule ID search | P1 | S | planned | |
| B-032 | Synonym dictionary | P2 | M | idea | |

### E5 — Trust & light workflow

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-033 | Confidence legend + disclaimers on intel/Intune | P0 | S | done | ConfidenceLegend + Intune disclaimer |
| B-034 | “Needs human review” on low-confidence data | P0 | S | planned | |
| B-035 | Richer provenance UI (SHA, library name, build) | P1 | S | idea | meta exists |
| B-036 | Check vs fix visual separation | P2 | S | idea | |
| B-037 | Personal scratch notes / status (local only) | P2 | M | idea | Not STIG Manager |
| B-038 | Local checklist → CSV export | P3 | M | idea | |
| B-039 | Outbound links to STIG Manager / formal tools | P2 | S | idea | |

### E6 — Performance & polish

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-040 | Search index in Web Worker | P0 | M | planned | |
| B-041 | Compressed / sharded search index | P1 | L | planned | |
| B-042 | Offline shell (service worker) | P3 | L | idea | |
| B-043 | Mobile layout improvements | P1 | M | idea | |
| B-044 | Theme / high-contrast polish | P2 | S | idea | Carbon default done |
| B-045 | Skeleton loaders | P2 | S | idea | |

### E7 — Content breadth

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-046 | Mid-cycle individual STIG ZIP ingest | P1 | M | planned | |
| B-047 | SRG vs STIG filter | P2 | S | idea | |
| B-048 | Sunset / superseded badges | P1 | S | planned | Needs multi-release |
| B-049 | Vendor product landing pages | P2 | M | idea | |
| B-050 | SCAP/OVAL presence badge | P3 | S | idea | |

### E8 — Collaboration

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-051 | Embeddable rule card snippet | P2 | M | idea | |
| B-052 | Team pack JSON (rule list import/export) | P2 | M | idea | |
| B-053 | Map / intel contribution checklist | P2 | S | idea | |
| B-054 | Automated release notes from meta + diff | P1 | M | planned | |

### E9 — Threat intel enrichment (new)

Associate **public** security context with rules where evidence exists. Always labeled: source, date, confidence, “not a finding substitute”.

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-060 | **CVE linkage** per rule (from XCCDF `ident` + enrichment) | P0 | M | done | NVD links |
| B-061 | **CISA KEV** flag when CVE ∈ KEV catalog | P0 | M | done | User: “KEVD” → KEV |
| B-062 | **MITRE ATT&CK** technique suggestions per rule | P1 | L | planned | Map via control/CCI/keyword + curated |
| B-063 | **Public PoC references** (advisory links, not weaponized code) | P1 | L | planned | Link-out only |
| B-064 | **IoCs** (public indicators) linked when relevant | P2 | L | idea | Careful: scope/noise |
| B-065 | **Open-source “pwned” / incident reports** (writeups, CISA alerts) | P1 | L | planned | Curated + URL allowlist |
| B-066 | Threat intel panel on rule UI | P0 | M | done | CVE + KEV v1 |
| B-067 | Quarterly intel rebuild (with STIG library build) | P0 | M | done | KEV fetch in build |
| B-068 | Search/filter: has-CVE, in-KEV, has-ATT&CK | P1 | S | done | CVE + KEV filters (ATT&CK later) |
| B-069 | Product-level threat summary export | P2 | M | idea | |
| B-070 | Intel contribution YAML schema | P1 | M | planned | Like intune_maps |

### E10 — Review follow-ups (July 2026)

From [REVIEW_2026-07.md](REVIEW_2026-07.md).

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-071 | Scheduled KEV refresh workflow + hardened fetch | P0 | M | done | `kev-refresh.yml`, retry/validate/safe cache |
| B-072 | Pipeline error-handling pass (no silent stage drops) | P0 | M | done | error-level logs; narrow catches |
| B-073 | Supply-chain hygiene (pin deps, Dependabot, SHA Actions, no prod maps) | P0 | S | done | requirements pin + dependabot + sourcemap off |
| B-074 | Frontend UX/a11y (retry, skip link, live regions, KEV pagination) | P1 | M | done | ErrorRetry, skip link, live region, KEV show-more, debounce, aria-pressed |
| B-075 | Frontend + pipeline test suites in CI | P1 | L | done | Vitest 20 tests + pytest CI; ZIP fixture later |
| B-076 | Build emits size metrics into meta.json | P2 | S | done | Uncompressed inventory; gzip budget still future |

---

## Already shipped (baseline — not backlog)

- Static Pages site, MiniSearch, STIG/rule deep links  
- Tags, vendor/role filters, quick links  
- Intune CSP v1 (quick-link products, catalog seed, product export)  
- Carbon theme default, multi-theme switcher  
- Family keys, VERSION_HISTORY design doc  

---

## Explicit backlog: “all MS Windows STIGs”

Tracked as **B-012**. Do not expand Intune processing to full Microsoft set until quick-link maps are healthier and export UX is solid (B-010, B-011, B-016).
