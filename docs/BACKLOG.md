# stigref product backlog

**Last updated:** 2026-07-10  
**Status:** Living document  
**Product:** [stigref](https://github.com/edoDev/stigref) — static STIG reference (search, deep links, copy, Intune CSP hints)

**July 2026 review:** [REVIEW_2026-07.md](REVIEW_2026-07.md)  
**Session resume:** [SESSION_LOG.md](SESSION_LOG.md)  
**Contributing maps:** [CONTRIBUTING_MAPS.md](CONTRIBUTING_MAPS.md)

---

## How to use this backlog

| Field | Meaning |
|--------|---------|
| **ID** | Stable backlog id (`B-xxx`) |
| **Priority** | P0 now → P3 later / nice-to-have |
| **Size** | S / M / L / XL (rough engineering effort) |
| **Status** | `idea` · `planned` · `in progress` · `done` · `wontfix` |

**Non-goals:** full assessment platform (STIG Manager), CUI content, live cyber.mil at browse time, unvetted threat intel as findings.

---

## Full backlog

### E1 — Daily UX

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-001 | Saved searches / bookmarks | P0 | M | done | |
| B-002 | Shareable search URLs | P0 | S | done | |
| B-003 | Rule comparison | P1 | L | done | `/compare` |
| B-004 | Related rules | P1 | M | done | |
| B-005 | Copy packs | P0 | S | done | |
| B-006 | Keyboard-first UX | P1 | M | done | |
| B-007 | Print / PDF rule view | P2 | S | done | |
| B-008 | Severity / CCI filters | P0 | M | done | |
| B-009 | Open in Intune recipes | P1 | M | done | |
| B-010 | Intune coverage meter | P0 | S | done | |

### E2 — Intune / CSP

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-011 | Expand curated maps | P0 | L | done | |
| B-012 | MS Windows STIG Intune process | P1 | L | done | |
| B-013 | Settings Catalog names beside OMA-URI | P1 | M | done | area/name on suggestions |
| B-014 | Multi-option ranking | P1 | M | done | |
| B-015 | Conflict warnings | P2 | M | done | Product hub OMA-URI value conflicts |
| B-016 | Intune baseline pack export | P0 | M | done | |
| B-017 | Map contribution helper | P2 | M | done | Tools page YAML helper |
| B-018 | CSP catalog refresh runbook | P1 | L | done | |
| B-019 | Chrome / Office maps | P2 | L | done | |
| B-020 | Verify in Windows PS hints | P2 | M | done | Rule page templates |

### E3 — Version history

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-021 | Multi-release storage | P0 | L | done | Foundation |
| B-022 | What-changed report | P0 | L | done | |
| B-023 | Family previous versions | P1 | M | done | |
| B-024 | Changelog page | P1 | S | done | `/releases` |
| B-025 | Watchlist | P3 | L | done | Local; cross-release when 2 catalogs |

### E4 — Discovery

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-026 | Faceted search | P0 | M | done | |
| B-027 | CCI browser | P1 | L | done | `/cci` |
| B-028 | NIST 800-53 fixtures | P2 | L | done | `/nist` stub |
| B-029 | Product hubs | P0 | M | done | |
| B-030 | Recently viewed | P1 | S | done | |
| B-031 | Typo-tolerant rule ID | P1 | S | done | |
| B-032 | Synonym dictionary | P2 | M | done | Alternate queries |

### E5 — Trust & light workflow

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-033 | Confidence legend | P0 | S | done | |
| B-034 | Needs human review | P0 | S | done | |
| B-035 | Provenance UI | P1 | S | done | |
| B-036 | Check vs fix separation | P2 | S | done | |
| B-037 | Personal scratch notes | P2 | M | done | Local notes on rule |
| B-038 | Checklist CSV export | P3 | M | done | Tools page |
| B-039 | STIG Manager links | P2 | S | done | |

### E6 — Performance & polish

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-040 | Search Web Worker | P0 | M | done | |
| B-041 | Compressed / sharded index | P1 | L | wontfix | Deferred: 21MB docs OK; shard later if needed |
| B-042 | Offline shell (SW) | P3 | L | done | App-shell SW; data network-first |
| B-043 | Mobile layout | P1 | M | done | |
| B-044 | Carbon theme locked | P2 | S | done | |
| B-045 | Skeleton loaders | P2 | S | done | |

### E7 — Content breadth

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-046 | Mid-cycle STIG ZIP ingest | P1 | M | done | |
| B-047 | SRG vs STIG filter | P2 | S | done | |
| B-048 | Sunset / superseded badges | P1 | S | done | Family V/R compare |
| B-049 | Vendor landing pages | P2 | M | done | `/vendors` |
| B-050 | SCAP/OVAL badge | P3 | S | idea | No SCAP data in public U_ library reliably |

### E8 — Collaboration

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-051 | Embeddable rule card | P2 | M | done | Copy embed HTML on rule |
| B-052 | Team pack JSON | P2 | M | done | Tools import/export |
| B-053 | Contribution checklist | P2 | S | done | |
| B-054 | Automated release notes | P1 | M | done | |

### E9 — Threat intel

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-060 | CVE linkage | P0 | M | done | |
| B-061 | CISA KEV | P0 | M | done | |
| B-062 | ATT&CK suggestions | P1 | L | done | Keyword + curated maps |
| B-063 | Public PoC references | P1 | L | done | intel_maps poc link-outs |
| B-064 | IoCs | P2 | L | done | intel_maps iocs (careful scope) |
| B-065 | Public incident reports | P1 | L | done | intel_maps references |
| B-066 | Threat panel UI | P0 | M | done | |
| B-067 | Quarterly intel rebuild | P0 | M | done | |
| B-068 | has-CVE / KEV / ATT&CK filters | P1 | S | done | hasAttack filter |
| B-069 | Product threat summary export | P2 | M | done | Product hub button |
| B-070 | Intel YAML schema | P1 | M | done | |

### E10 — Review follow-ups

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-071 | Scheduled KEV refresh | P0 | M | done | |
| B-072 | Pipeline error handling | P0 | M | done | |
| B-073 | Supply-chain hygiene | P0 | S | done | |
| B-074 | Frontend a11y/UX | P1 | M | done | |
| B-075 | CI test suites | P1 | L | done | |
| B-076 | Size metrics in meta | P2 | S | done | |

---

### E11 — Framework crosswalks

| ID | Feature | Pri | Size | Status | Notes |
|----|---------|-----|------|--------|-------|
| B-080 | CIS Benchmark side-by-side + content maps | P0 | L | done | `cis_maps/`, `/cis`, rule panel, CSV/MD export |
| B-081 | Expand CIS map coverage | P1 | L | planned | Ongoing content |
| B-082 | Optional local CIS PDF extract (gitignored) | P2 | L | idea | License-gated full text |

## Remaining open

| ID | Status | Why open |
|----|--------|----------|
| **B-050** | idea | SCAP/OVAL not consistent in public U_ library |
| **B-081** | planned | More CIS seed rows / products |
| **B-082** | idea | Full CIS body only via license-safe local path |

Product surface is largely complete. Ongoing work is **map content** (CIS + Intune) and the next DISA quarterly import.
