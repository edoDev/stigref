# Local CIS extracts (B-082)

Public stigref ships **mapping-only** CIS crosswalks (`scripts/stigref_build/cis_maps/`).  
For **private** builds you may place longer CIS recommendation text under `raw/cis/` (gitignored).

## Setup

1. Create `raw/cis/` (already under ignored `raw/`).
2. Add JSON files matching `scripts/stigref_build/cis_maps/local_extract.schema.json`.
3. Run `python scripts/reapply_cis.py`.
4. Rule page CIS items with matching IDs gain `localDescription` / `localAudit` / `localRemediation`.

## Rules

- Do **not** commit CIS PDFs or full extracts to a public remote.
- Curated maps still define *which* STIG↔CIS links exist; local extracts only enrich text.
- Official CIS Benchmark remains authoritative for assessment.
