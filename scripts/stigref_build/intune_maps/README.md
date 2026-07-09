# Intune mapping YAML (community-editable)

Each file maps **STIG rules → Intune CSP suggestions** for a product (quick-link id).

## Schema

```yaml
product: windows-11          # matches curated_tags quick_links id
family: microsoft-windows-11 # optional family key
version: "1"                 # map file version
notes: |
  Short maintainer notes.

rules:
  - rule_id: SV-253260          # prefix match on full_rule_id OK
    # or full_rule_id: SV-253260r1186370_rule
    suggestions:
      - csp_id: Policy.BitLocker.SystemDrivesRequireStartupAuthentication
        value: "see Learn / ADMX payload"
        confidence: high          # high | medium | low
        kind: native              # native | admx-backed | settings-catalog
        rationale: STIG requires BitLocker PIN pre-boot auth.
        # optional overrides:
        # omaUri: ./Device/...
        # learnUrl: https://...
        # title: ...
```

## Matching

1. **Curated** rows in these files (highest priority).
2. **Heuristic** registry/keyword match against `csp/catalog_seed.json` during build.

## Coverage target (v1)

Quick-link products only. Expanding to all Microsoft Windows STIGs is backlog.
