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
3. Backlog: enable processing for all Microsoft Windows STIGs (`should_process_stig`).

## Disclaimer

Suggestions are **assistive**. STIG checks remain authoritative. CSP names/values change across Windows builds — follow the Learn usage pages before production deploy.
