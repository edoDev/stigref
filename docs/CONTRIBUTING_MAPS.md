# Contributing Intune maps & intel (B-053)

## Intune CSP maps

1. Pick a product file under `scripts/stigref_build/intune_maps/` (quick-link id).
2. Follow the schema in `intune_maps/README.md` (`rule_id` + `suggestions` with `csp_id`).
3. Prefer **native** Policy CSP over ADMX when both exist; set `confidence` honestly.
4. Never invent OMA-URI paths — copy from Learn or `csp/catalog_seed.json`.
5. Run `python scripts/reapply_intune.py` and spot-check a product hub + rule page.
6. Open a PR; mention backlog id (e.g. B-011) in the commit message.

## Threat intel maps

1. See `scripts/stigref_build/intel_maps/README.md` (B-070 schema).
2. Link-outs only — no exploit code, no paid/proprietary dumps.
3. Always include confidence + source + disclaimer language.

## Checklist before merge

- [ ] YAML parses (build or reapply does not error)
- [ ] Rule IDs exist in current catalog (or noted as forward-looking)
- [ ] Learn / MITRE / CISA URLs resolve
- [ ] UI shows expected badges (confidence, review)
- [ ] No secrets or CUI
