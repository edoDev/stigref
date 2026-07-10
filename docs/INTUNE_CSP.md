# Intune CSP suggestions

## Decisions (locked)

| # | Choice |
|---|--------|
| Scope v1 | Quick-link products only; all Microsoft Windows STIGs on backlog |
| Option display | Show all options with kind badges (`native` / `admx-backed` / `settings-catalog`) |
| Catalog | Hybrid: ship `data/csp/catalog.json` + always link to Microsoft Learn |
| Mapping | Curated YAML + heuristic (registry/keywords) with confidence |
| Empty state | “No mapping yet” + Policy CSP search link |
| Export | Product-level JSON under `data/intune/products/{id}.json` |
| Maintenance | Curated maps reviewed by maintainers; community-editable YAML |
| Attribution | Short derived descriptions + Learn links (not full Learn HTML scrape) |
| Timing | Evaluated **during STIG data build** each quarterly library processing |

## Pipeline

```
XCCDF parse → enrich tags → attach_intune_to_stigs() → write rules + intune exports
```

Inputs:

- `scripts/stigref_build/csp/catalog_seed.json` — CSP index (OMA-URI, Learn URL, registry hints)
- `scripts/stigref_build/intune_maps/*.yaml` — curated rule → CSP rows

Outputs:

- `data/csp/catalog.json`
- `data/rules/by-id/*.json` → `intune` block (quick-link products)
- `data/intune/products/{quicklink_id}.json` — exportable policy draft
- `data/intune/index.json`

## UI

- Rule page: **Intune / CSP suggestions** under Fix (multi-option callout, Learn links, copy OMA-URI/value)
- STIG page (quick-link products): **Export Intune JSON**

## Expanding coverage

1. Add curated rows to the product YAML when validated.
2. Grow `catalog_seed.json` with more Policy CSP entries (registry paths help heuristics).
3. **B-012:** `should_process_stig` also processes Microsoft Windows / Edge / Defender / Office / Chrome STIGs (heuristics) plus `intune-companion` tags — not only quick-links.
4. After map edits without a full library rebuild: `python scripts/reapply_intune.py`

## B-018 — CSP catalog refresh runbook (quarterly)

Run with each DISA library import (or when Microsoft documents major CSP renames).

1. **Collect sources**
   - Microsoft Learn Policy CSP index: https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-configuration-service-provider
   - Optional: export Settings Catalog definition IDs from a lab tenant / Graph (do not commit secrets).
2. **Update seed**
   - Edit `scripts/stigref_build/csp/catalog_seed.json`.
   - For each entry: `id`, `omaUriDevice` (or user), `learnUrl`, `keywords`, `registryPaths` when known.
   - Prefer additive changes; mark deprecated CSPs in `description` rather than deleting IDs used by maps.
3. **Validate maps**
   - Grep intune_maps for `csp_id` values missing from the seed.
   - `cd scripts && python -m pytest tests/test_intune_suggest.py -q`
4. **Rebuild / reapply**
   - Full: `python -m stigref_build -i raw/U_SRG-STIG_Library_….zip -o ../data --release YYYY-MM`
   - Maps only: `python reapply_intune.py`
5. **Ship**
   - Commit `catalog_seed.json`, maps, and regenerated `data/intune/**` + affected rules.
   - Note in release notes on `/releases` (B-024).

## Disclaimer

Suggestions are **assistive**. STIG checks remain authoritative. CSP names/values change across Windows builds — follow the Learn usage pages before production deploy.
