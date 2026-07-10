# Multi-release history design (next library update)

## Goal

When a new quarterly `U_SRG-STIG_Library_*.zip` is ingested, keep **previous** catalog data so users can:

- Open the current STIG version
- Compare or browse the previous version of the same **family**
- Review what changed (added/removed/changed rules)

## Why not only overwrite `data/`

Today `data/` is the live catalog. Overwriting loses prior V/R. Deep links to old STIG ids break only if ids change (they include version+release+hash, so old ids can remain if we **keep files**).

## Proposed layout

```
data/
  meta.json                 # points at current release id
  current/                  # OR keep flat as today for current
    stigs/ rules/ search/ tags/ families/
  releases/
    2026-04/                # from U_SRG-STIG_Library_April_2026
      meta.json
      stigs/ rules/ search/ ...
    2026-07/
      ...
  diffs/
    2026-04__2026-07.json   # family-level + rule-level summary
```

### `meta.json` (root)

```json
{
  "currentRelease": "2026-07",
  "releases": [
    { "id": "2026-07", "label": "July 2026", "sourceFile": "U_SRG-STIG_Library_July_2026.zip" },
    { "id": "2026-04", "label": "April 2026", "sourceFile": "U_SRG-STIG_Library_April_2026.zip" }
  ],
  "lastUpdated": "..."
}
```

### Family map

Already started: `data/families/index.json` groups STIGs by title-derived `family` key (version-agnostic). Across releases, same family may have multiple STIG ids (V2R7 vs V2R8).

### Diff artifact

```json
{
  "from": "2026-04",
  "to": "2026-07",
  "families": [
    {
      "family": "microsoft-windows-11",
      "before": { "id": "...-v2r7-...", "version": "2", "release": "7" },
      "after": { "id": "...-v2r8-...", "version": "2", "release": "8" },
      "rules": {
        "added": ["SV-..."],
        "removed": ["SV-..."],
        "changed": [{ "id": "SV-...", "fields": ["check", "fix"] }]
      }
    }
  ]
}
```

## UI (later)

- STIG detail: “Other versions in catalog” from `families`
- Optional release switcher in header
- Diff page: `/diff/2026-04/2026-07` or per-family

## Build pipeline changes

1. `build_data.py --release 2026-07 --input raw/...zip --out data/releases/2026-07`
2. `promote_current.py` copies or symlinks release → `data/` live tree (or UI reads `meta.currentRelease`)
3. `diff_releases.py --from 2026-04 --to 2026-07`

## Size note

Each full release ≈ 100 MB. Keeping 2–4 quarters on GitHub is workable; older quarters can move to GitHub Releases artifacts.

## Current status (B-021 foundation — 2026-07)

- **April 2026** is the live `data/` tree (`storage: live`).
- Root `meta.json` includes `currentRelease`, `release`, and `releases[]`.
- Registry: `data/releases/index.json` + `data/releases/2026-04/pointer.json` (no full tree copy yet — avoids doubling ~117 MB in git).
- CLI: `python -m stigref_build --release 2026-07 -o data/releases/2026-07 …`
- Promote: `python promote_current.py --from data/releases/2026-07`
- Diff (family-level): `python diff_releases.py --from data --to data/releases/2026-07`
- UI: header shows release label when present.
- **Next library import:** build into `data/releases/{id}/`, archive prior live snapshot (git tag or GH Release asset), then promote.
