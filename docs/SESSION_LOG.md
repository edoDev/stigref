# stigref session log (resumable)

## Resume pointer

| Field | Value |
|-------|--------|
| **Session** | 2026-07-10 Library Observatory (B-090) |
| **Last completed portion** | Full Insights feature shipped + data generated |
| **Next portion** | Optional: content refinement, next DISA import (delta charts) |
| **Branch** | `main` |
| **Last known good commit** | *(see git log after push)* |

---

## B-090 Library Observatory

- Pipeline: `scripts/stigref_build/insights.py` + `scripts/build_insights.py`
- Data: `data/stats/insights.json` (scanned 303 STIGs / 19,403 rules)
- UI: `/insights` — KPI strip, landscape, Intune surface, automation, CIS/CCI/ATT&CK, KEV, health/delta, board-pack export
- Wired into `write_data` (post-build scan)

---

## Claude review (July 2026) — closed

Canonical disposition: [REVIEW_2026-07.md](REVIEW_2026-07.md)
