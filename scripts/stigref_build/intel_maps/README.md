# Intel contribution maps (B-070)

Curated YAML linking public threat context to STIG rules or CVEs.

## Schema (`*.yaml`)

```yaml
version: "1"
# Optional scope
cve: CVE-2021-34527          # and/or
rule_id: SV-253260           # prefix match on full_rule_id

attack:
  - techniqueId: T1003
    name: OS Credential Dumping
    url: https://attack.mitre.org/techniques/T1003/
    confidence: medium       # high | medium | low
    source: curated

references:
  - type: advisory           # advisory | writeup | cisa-aa | nvd
    title: CISA alert title
    url: https://www.cisa.gov/...
    publisher: CISA
    date: "2021-07-01"

# Never include weaponized PoC payloads — link-outs only
poc:
  - title: Public analysis writeup
    url: https://example.com/analysis
    note: Link only; not an exploit package

iocs: []                     # optional public indicators (hashes/domains) with sourceUrl
disclaimer: >
  Public context only. Not a vulnerability scan result.
```

## Rules

1. Prefer **link-outs** to public sources (CISA, NVD, MITRE, vendor advisories).
2. Always set **confidence** and **source**.
3. Do not paste proprietary / paid intel or malware samples.
4. Reviewers: reject entries that present intel as a STIG finding.

Pipeline loaders may merge these into `rule.threat` on the next quarterly build.
