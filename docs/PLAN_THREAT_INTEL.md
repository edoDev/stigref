# Threat intel enrichment plan (CVE, KEV, ATT&CK, PoC, IoC, public reports)

**Backlog epic:** E9 (B-060 … B-070)  
**Principle:** Enrich rules with **public, attributable** context. Never present intel as a STIG finding or as proof of compromise.

User request mapping:

| You said | We interpret as |
|----------|------------------|
| CVE | CVE IDs linked to the rule / control |
| KEVD | **CISA KEV** (Known Exploited Vulnerabilities catalog) |
| MITRE ATT&CK | Techniques/tactics relevant to the misconfiguration |
| Commonly known PoCs | **Links** to public PoC writeups/advisories (not hosting exploit code) |
| IoT’s | **IoCs** (Indicators of Compromise) *or* IoT-device notes — default **IoCs**; flag IoT product STIGs separately |
| Open source “pwned” reports | Public incident reports, CISA alerts, GHSA, reputable postmortems |

---

## Goals

1. On a **rule page**, show a **Threat context** panel when data exists.  
2. Rebuild intel **with each quarterly STIG library build** (same cadence as Intune).  
3. Support **filter/search**: has CVE, in KEV, has ATT&CK.  
4. Prefer **link-outs + IDs** over copying large proprietary datasets into git.

---

## Non-goals

- Shipping exploit code, weaponized PoCs, or malware samples  
- Guaranteeing completeness of CVE↔STIG mapping  
- Real-time threat feeds in the browser (CORS, ToS, rate limits)  
- Replacing vulnerability scanners or TIP platforms  

---

## Data sources (public)

| Signal | Source | License / access | Build use |
|--------|--------|------------------|-----------|
| CVE on rule | Already in XCCDF `ident` (CVE system) | Public STIG | Primary |
| CVE metadata | [NVD API](https://nvd.nist.gov/developers) / CVE.org | Public, rate limits | Optional enrich (CVSS, CWE, dates) |
| KEV | [CISA KEV JSON](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | Public | Flag `inKev: true` |
| ATT&CK | [MITRE ATT&CK STIX/JSON](https://github.com/mitre/cti) | Open | Technique suggest + link |
| PoC / advisories | NVD references, CISA AA, vendor advisories, GHSA | Public URLs only | Allowlisted domains |
| IoCs | CISA/malware analysis reports (published IoCs) | Public | Curated YAML per CVE/family |
| “Pwned” reports | CISA, NCSC, vendor blogs, academic writeups | Public | Curated links + titles |

**IoT ambiguity:**  
- **IoCs** = indicators (hashes, domains, etc.) on the threat panel.  
- **IoT devices** = product role tag / filter for IoT-related STIGs (separate, lighter).

---

## Architecture

```
STIG build
  ├─ parse XCCDF (existing) → rule.ccis, rule.cves
  ├─ load intel/
  │    ├─ kev.json              (downloaded quarterly)
  │    ├─ attack/techniques.json (subset or full ATT&CK)
  │    └─ maps/*.yaml           (curated rule/CVE → ATT&CK, reports, IoCs)
  ├─ enrich_threat(rule) → rule.threat
  └─ write data/rules/… + data/threat/index.json + search fields
```

### `rule.threat` shape (v1)

```json
{
  "status": "mapped" | "none",
  "cves": [
    {
      "id": "CVE-2021-34527",
      "inKev": true,
      "cvss": { "version": "3.1", "score": 8.8, "severity": "HIGH" },
      "nvdUrl": "https://nvd.nist.gov/vuln/detail/CVE-2021-34527",
      "kevUrl": "https://www.cisa.gov/..."
    }
  ],
  "attack": [
    {
      "techniqueId": "T1068",
      "name": "Exploitation for Privilege Escalation",
      "url": "https://attack.mitre.org/techniques/T1068/",
      "confidence": "medium",
      "source": "curated" | "heuristic"
    }
  ],
  "references": [
    {
      "type": "advisory" | "poc_writeup" | "incident" | "ioc_report",
      "title": "...",
      "url": "https://...",
      "publisher": "CISA",
      "date": "2021-07-01"
    }
  ],
  "iocs": [
    {
      "type": "domain" | "sha256" | "ip" | "other",
      "value": "...",
      "sourceUrl": "https://...",
      "note": "From public CISA report; may be outdated"
    }
  ],
  "disclaimer": "Public context only. Not a vulnerability scan result."
}
```

### Search index fields

Add: `cveIds`, `inKev` (bool), `attackIds`, `hasThreat` for B-068 filters.

---

## Mapping strategy (like Intune)

| Layer | What | Confidence |
|-------|------|------------|
| **A. Native STIG** | CVE IDs in XCCDF | high for ID presence |
| **B. KEV join** | CVE ∈ KEV catalog | high for flag |
| **C. Curated YAML** | rule_id / cve → ATT&CK, reports, IoCs | high/medium |
| **D. Heuristic** | keywords (RDP, PrintNightmare, etc.) → ATT&CK | low/medium |

PoCs: **reference URLs only** (e.g. NVD ref, GitHub advisory). Do not vendor tarball exploits into the repo.

---

## UI

**Rule page — “Threat context” panel** (below Intune or tabbed with it):

1. CVE chips (red outline if KEV)  
2. ATT&CK techniques (links)  
3. Public reports / writeups list  
4. IoCs in monospace + source link + “may be outdated”  
5. Always: disclaimer + last intel build date from `data/threat/meta.json`

**Empty state:** “No public CVE/ATT&CK context linked for this rule.”

**STIG / product hub:** counts — `# CVEs`, `# in KEV`, top techniques.

---

## Quarterly pipeline steps (ops)

1. Download STIG library (existing).  
2. Download CISA KEV JSON → `raw/intel/kev.json` (gitignored) or fetch in CI.  
3. Optionally refresh ATT&CK STIX subset.  
4. Run `stigref_build` (STIG + Intune + threat enrich).  
5. Review `data/threat/meta.json` counts; spot-check KEV hits.  
6. Commit `data/` (or release artifact if size blows up).

---

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Stale IoCs | Date + source; “not for blocking without validation” |
| Wrong ATT&CK mapping | Confidence labels; curated over heuristic |
| Repo size | Store links + IDs; not full NVD dumps |
| Legal / ToS | Public sources only; attribution in About |
| Alarm fatigue | KEV badge only for true KEV CVEs; don’t mark every rule critical |
| PoC abuse | Link-only; no exploit code in repo |

---

## Phased delivery

| Phase | Deliverable | Backlog |
|-------|-------------|---------|
| **T0** | Surface existing `rule.cves` in UI + NVD links | B-060 partial |
| **T1** | KEV join + badge + filter | B-061, B-066, B-068 |
| **T2** | Curated ATT&CK + reports YAML schema | B-062, B-065, B-070 |
| **T3** | PoC writeup allowlist + IoC optional blocks | B-063, B-064 |
| **T4** | Product threat summary export | B-069 |

**Schedule relative to B-001…B-020:**  
Run **T0–T1 in parallel with W1** (cheap, high value). Deeper ATT&CK/IoC after Intune map growth (B-011).

---

## Acceptance (epic done)

- [ ] Rules with STIG CVEs show links  
- [ ] KEV membership visible and filterable  
- [ ] At least one product has curated ATT&CK + report examples  
- [ ] Quarterly rebuild documented with STIG zip steps  
- [ ] No exploit payloads in repository  
