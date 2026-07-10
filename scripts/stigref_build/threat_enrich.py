"""Enrich rules with CVE display metadata and CISA KEV membership."""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

KEV_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/"
    "known_exploited_vulnerabilities.json"
)
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.I)
NVD = "https://nvd.nist.gov/vuln/detail/"
KEV_CATALOG = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"

# Retry policy for network fetch (transient outages)
KEV_FETCH_RETRIES = 3
KEV_FETCH_BACKOFF_SEC = 2.0
# Sanity floor: CISA KEV has been well above this for years
KEV_MIN_VULNS = 100


def normalize_cve(cve: str) -> str:
    m = CVE_RE.search(cve or "")
    if m:
        return m.group(0).upper()
    return (cve or "").strip().upper()


def validate_kev_payload(data: Any) -> dict[str, Any]:
    """
    Validate CISA KEV JSON shape. Raises ValueError on bad/incomplete data.
    """
    if not isinstance(data, dict):
        raise ValueError("KEV payload must be a JSON object")
    vulns = data.get("vulnerabilities")
    if not isinstance(vulns, list):
        raise ValueError("KEV payload missing 'vulnerabilities' list")
    if len(vulns) < KEV_MIN_VULNS:
        raise ValueError(
            f"KEV vulnerabilities count {len(vulns)} below minimum {KEV_MIN_VULNS}"
        )
    sample = vulns[0]
    if not isinstance(sample, dict) or not sample.get("cveID"):
        raise ValueError("KEV first entry missing cveID")
    # Spot-check a mid entry if present
    mid = vulns[len(vulns) // 2]
    if not isinstance(mid, dict) or not mid.get("cveID"):
        raise ValueError("KEV mid entry missing cveID")
    return data


def _load_kev_cache(cache_path: Path) -> dict[str, Any] | None:
    """Read and validate KEV cache; return None on any failure (never raise)."""
    try:
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
        return validate_kev_payload(raw)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        log.error("KEV cache invalid or unreadable at %s: %s", cache_path, exc)
        return None


def _fetch_kev_json(*, timeout: int = 60) -> dict[str, Any]:
    """
    Download and validate KEV JSON with retries.
    Raises the last network/parse/validation error if all attempts fail.
    """
    last_exc: BaseException | None = None
    req = urllib.request.Request(
        KEV_URL,
        headers={"User-Agent": "stigref-build/0.1 (threat enrich)"},
    )
    for attempt in range(1, KEV_FETCH_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
            data = validate_kev_payload(json.loads(body))
            return data
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
            UnicodeError,
            ValueError,
        ) as exc:
            last_exc = exc
            log.warning(
                "KEV download attempt %s/%s failed: %s",
                attempt,
                KEV_FETCH_RETRIES,
                exc,
            )
            if attempt < KEV_FETCH_RETRIES:
                time.sleep(KEV_FETCH_BACKOFF_SEC * attempt)
    assert last_exc is not None
    raise last_exc


def _fetch_or_load_kev(
    cache_path: Path | None = None,
    *,
    fetch: bool = True,
    timeout: int = 60,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    meta: dict[str, Any] = {
        "source": KEV_URL,
        "catalogUrl": KEV_CATALOG,
        "fetchedAt": None,
        "count": 0,
        "fromCache": False,
    }
    data: dict[str, Any] | None = None

    if fetch:
        try:
            data = _fetch_kev_json(timeout=timeout)
            meta["fetchedAt"] = (
                datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    json.dumps(data), encoding="utf-8"
                )
            log.info(
                "Downloaded CISA KEV catalog (%s vulnerabilities)",
                len(data.get("vulnerabilities") or []),
            )
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
            UnicodeError,
            ValueError,
        ) as exc:
            log.error(
                "KEV download failed after %s attempts: %s — trying cache",
                KEV_FETCH_RETRIES,
                exc,
            )
            meta["fetchError"] = str(exc)

    if data is None and cache_path and cache_path.is_file():
        data = _load_kev_cache(cache_path)
        if data is not None:
            meta["fromCache"] = True
            log.info("Loaded KEV from cache %s", cache_path)
        else:
            meta["cacheError"] = True

    if data:
        meta["catalogVersion"] = data.get("catalogVersion")
        meta["dateReleased"] = data.get("dateReleased")
        meta["count"] = len(data.get("vulnerabilities") or [])
    else:
        log.error(
            "No KEV data available (fetch failed and cache missing/invalid)"
        )
    return data, meta


def normalize_kev_entries(
    data: dict[str, Any] | None,
    *,
    cve_to_rules: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Flatten CISA KEV rows for the static site browser."""
    cve_to_rules = cve_to_rules or {}
    out: list[dict[str, Any]] = []
    if not data:
        return out
    for row in data.get("vulnerabilities") or []:
        if not isinstance(row, dict):
            continue
        cve = normalize_cve(row.get("cveID") or "")
        if not cve:
            continue
        out.append(
            {
                "cveID": cve,
                "vendorProject": row.get("vendorProject") or "",
                "product": row.get("product") or "",
                "vulnerabilityName": row.get("vulnerabilityName") or "",
                "dateAdded": row.get("dateAdded") or "",
                "shortDescription": row.get("shortDescription") or "",
                "requiredAction": row.get("requiredAction") or "",
                "dueDate": row.get("dueDate") or "",
                "knownRansomwareCampaignUse": row.get(
                    "knownRansomwareCampaignUse"
                )
                or "",
                "notes": row.get("notes") or "",
                "cwes": row.get("cwes") or [],
                "nvdUrl": f"{NVD}{cve}",
                "linkedRules": cve_to_rules.get(cve) or [],
            }
        )
    out.sort(key=lambda r: (r.get("dateAdded") or "", r["cveID"]), reverse=True)
    return out


def load_kev_ids(
    cache_path: Path | None = None,
    *,
    fetch: bool = True,
    timeout: int = 60,
) -> tuple[set[str], dict[str, Any]]:
    """Load set of CVE IDs in CISA KEV (backward compatible)."""
    data, meta = _fetch_or_load_kev(cache_path, fetch=fetch, timeout=timeout)
    ids: set[str] = set()
    if data:
        for row in data.get("vulnerabilities") or []:
            if not isinstance(row, dict):
                continue
            cve = normalize_cve(row.get("cveID") or "")
            if cve:
                ids.add(cve)
        meta["count"] = len(ids)
    return ids, meta


def load_kev_bundle(
    cache_path: Path | None = None,
    *,
    fetch: bool = True,
    timeout: int = 60,
    cve_to_rules: dict[str, list[str]] | None = None,
) -> tuple[set[str], dict[str, Any], list[dict[str, Any]]]:
    """Return (ids, meta, normalized entries for site catalog)."""
    data, meta = _fetch_or_load_kev(cache_path, fetch=fetch, timeout=timeout)
    ids: set[str] = set()
    if data:
        for row in data.get("vulnerabilities") or []:
            if not isinstance(row, dict):
                continue
            cve = normalize_cve(row.get("cveID") or "")
            if cve:
                ids.add(cve)
        meta["count"] = len(ids)
    entries = normalize_kev_entries(data, cve_to_rules=cve_to_rules)
    return ids, meta, entries


# Lightweight ATT&CK technique seeds (B-062). Prefer specific phrases (avoid "admin"/"password").
ATTACK_MITRE = "https://attack.mitre.org/techniques/"
# keyword (lowercase) → technique id + name — keep specific to limit noise
ATTACK_KEYWORD_SEED: list[tuple[str, str, str]] = [
    ("bitlocker", "T1486", "Data Encrypted for Impact"),
    ("credential dumping", "T1003", "OS Credential Dumping"),
    ("lsass", "T1003.001", "LSASS Memory"),
    ("remote desktop", "T1021.001", "Remote Desktop Protocol"),
    (" rdp ", "T1021.001", "Remote Desktop Protocol"),
    ("powershell script", "T1059.001", "PowerShell"),
    ("windows powershell", "T1059.001", "PowerShell"),
    ("smbv1", "T1210", "Exploitation of Remote Services"),
    ("smb v1", "T1210", "Exploitation of Remote Services"),
    ("smb1", "T1210", "Exploitation of Remote Services"),
    ("windows defender firewall", "T1562.004", "Disable or Modify System Firewall"),
    ("microsoft defender antivirus", "T1562.001", "Disable or Modify Tools"),
    ("smartscreen", "T1562.001", "Disable or Modify Tools"),
    ("user account control", "T1548.002", "Bypass User Account Control"),
    ("credential guard", "T1003", "OS Credential Dumping"),
    ("wdigest", "T1003", "OS Credential Dumping"),
    ("ntlmv1", "T1110", "Brute Force"),
    ("lanman authentication", "T1110", "Brute Force"),
    ("print spooler", "T1068", "Exploitation for Privilege Escalation"),
    ("anonymous sid", "T1078", "Valid Accounts"),
    ("guest account", "T1078", "Valid Accounts"),
]


def suggest_attack_for_rule(rule: dict[str, Any], *, limit: int = 4) -> list[dict[str, Any]]:
    """Keyword heuristic ATT&CK suggestions (public link-outs only)."""
    blob = " ".join(
        [
            rule.get("title") or "",
            rule.get("check") or "",
            rule.get("fix") or "",
            rule.get("description") or "",
            rule.get("group_title") or "",
        ]
    ).lower()
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for kw, tid, name in ATTACK_KEYWORD_SEED:
        if kw in blob and tid not in seen:
            seen.add(tid)
            path = tid.replace(".", "/")
            out.append(
                {
                    "techniqueId": tid,
                    "name": name,
                    "url": f"{ATTACK_MITRE}{path}/",
                    "confidence": "low",
                    "source": "keyword-seed",
                }
            )
        if len(out) >= limit:
            break
    return out


def build_threat_for_rule(
    rule: dict[str, Any],
    kev_ids: set[str],
) -> dict[str, Any]:
    raw = list(rule.get("cves") or [])
    # also scavenge free text for CVE ids
    blob = " ".join(
        [
            rule.get("title") or "",
            rule.get("check") or "",
            rule.get("fix") or "",
            rule.get("description") or "",
        ]
    )
    found = {normalize_cve(c) for c in raw if normalize_cve(c)}
    for m in CVE_RE.finditer(blob):
        found.add(m.group(0).upper())

    cves: list[dict[str, Any]] = []
    any_kev = False
    for cve_id in sorted(found):
        if not cve_id.startswith("CVE-"):
            continue
        in_kev = cve_id in kev_ids
        any_kev = any_kev or in_kev
        cves.append(
            {
                "id": cve_id,
                "inKev": in_kev,
                "nvdUrl": f"{NVD}{cve_id}",
                "kevUrl": KEV_CATALOG if in_kev else None,
            }
        )

    attack = suggest_attack_for_rule(rule)

    if not cves and not attack:
        return {
            "status": "none",
            "cves": [],
            "inKev": False,
            "attack": [],
            "references": [],
            "iocs": [],
            "disclaimer": (
                "Public context only. Not a vulnerability scan result."
            ),
        }

    return {
        "status": "mapped" if cves else "suggested",
        "cves": cves,
        "inKev": any_kev,
        "attack": attack,
        "references": [],
        "iocs": [],
        "disclaimer": (
            "Public CVE/KEV/ATT&CK context only. Keyword ATT&CK links are low-confidence "
            "suggestions — not a vulnerability scan result or STIG finding determination."
        ),
    }


def attach_threat_to_rules(
    rules_by_id: dict[str, dict],
    kev_ids: set[str],
) -> dict[str, int]:
    """Mutate rules with threat payloads. Returns stats."""
    with_cve = 0
    with_kev = 0
    for rule in rules_by_id.values():
        threat = build_threat_for_rule(rule, kev_ids)
        rule["threat"] = threat
        if threat.get("cves"):
            with_cve += 1
        if threat.get("inKev"):
            with_kev += 1
    return {
        "rulesWithCve": with_cve,
        "rulesWithKev": with_kev,
        "rulesTotal": len(rules_by_id),
    }
