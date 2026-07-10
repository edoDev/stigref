# CIS Benchmark crosswalk maps

Maps **STIG rules → CIS recommendation IDs** for side-by-side review in stigref.

## License / redistribution

- **Do not** commit full CIS Benchmark PDFs or proprietary XML into this public repo.
- Maps store **recommendation numbers**, short titles/notes **you author**, and relationship labels.
- Official CIS Benchmark documents remain authoritative (download via [CIS Workbench](https://workbench.cisecurity.org/)).

## Schema

```yaml
product: windows-11
cisBenchmark: "CIS Microsoft Windows 11 Enterprise Benchmark"
cisVersion: "3.0.0"       # version you validated against
profile: Level_1          # default profile for rows without override
notes: |
  Maintainer notes.

rules:
  - rule_id: SV-253284
    cis:
      - id: "18.9.95.1"
        title: "SEHOP is enabled (example ID — verify in your CIS PDF)"
        profile: Level_1          # optional override
        relationship: equivalent  # equivalent | related | partial | conflict
        confidence: high          # high | medium | low
        notes: Both require SEHOP; wording differs on …
```

## Relationships

| Value | Meaning |
|--------|---------|
| `equivalent` | Same control intent and expected outcome |
| `related` | Overlapping topic; not 1:1 |
| `partial` | CIS covers only part of the STIG (or vice versa) |
| `conflict` | Guidance may disagree — human review required |

## Build

Maps are applied during full library build and via:

```text
python scripts/reapply_cis.py
```
