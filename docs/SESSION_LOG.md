# stigref session log (resumable)

**Purpose:** Survive mid-session cutoffs. Next agent: read **Resume pointer** first.

---

## Resume pointer

| Field | Value |
|-------|--------|
| **Session date** | 2026-07-10 (wave 2) |
| **Goal** | B-021 → B-011 → B-040; Carbon lock; wider layout |
| **Last completed portion** | **S5** ship |
| **Next portion** | *(wave 2 complete)* Next candidates: B-022 rule-level diffs, B-012 full MS maps, B-062 ATT&CK |
| **Branch** | `main` |
| **Last known good commit** | *(set after push)* |
| **Repo dirty?** | Clean after S5 |

### How to resume

1. Read this **Resume pointer**.
2. If a portion is `IN PROGRESS`, re-run its verify steps.
3. Continue from **Next portion**.

---

## Wave 2 plan

| Portion | Scope | Status |
|---------|--------|--------|
| **S0** | Plan freeze + this log | DONE |
| **S1** | Carbon-only theme; remove picker; widen layout (`--max: 1280px`) | DONE |
| **S2** | B-021 multi-release: meta registry, CLI `--release`, promote/diff scripts, UI label | DONE |
| **S3** | B-011 expand Edge/Defender/Server maps + reapply intune | DONE |
| **S4** | B-040 MiniSearch in Web Worker | DONE |
| **S5** | Tests, backlog, commit, push | DONE |

### Out of scope this wave

- Full second DISA library import
- Duplicating 117 MB into `data/releases/{id}/` full trees in git
- ATT&CK epic, B-012 all Windows STIGs

---

## Portion journal

### S1 — Theme + width

- Carbon tokens on `:root` only; removed slate/violet/amber + header picker
- `--max: 960px` → **1280px**
- About/Help text updated

### S2 — B-021

- `write_data` emits `currentRelease` / `release` / `releases[]`
- `data/releases/index.json` + `2026-04/pointer.json` (storage=live)
- `promote_current.py`, `diff_releases.py`, CLI `--release`
- Header shows release label

### S3 — B-011

- Expanded maps: edge, defender-av, defender-fw, server-2019/2022/2025
- `reapply_intune.py` without full library parse
- Sample coverage: edge 11 mapped, defender-av 67, defender-fw 20, servers ~56–60

### S4 — B-040

- `searchCore.ts` + `search.worker.ts` + async `search.ts` API
- Build emits separate worker chunk (~20 KB)

### S5 — Verify

- pytest 34 · vitest 20 · production build OK
