"""Enrich rules with CVE display metadata and CISA KEV membership."""

from __future__ import annotations

import json
import logging
import re
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


def normalize_cve(cve: str) -> str:
    m = CVE_RE.search(cve or "")
    if m:
        return m.group(0).upper()
    return (cve or "").strip().upper()


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
    data = None

    if fetch:
        try:
            req = urllib.request.Request(
                KEV_URL,
                headers={"User-Agent": "stigref-build/0.1 (threat enrich)"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
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
            log.info("Downloaded CISA KEV catalog")
        except Exception as exc:  # noqa: BLE001
            log.warning("KEV download failed: %s", exc)

    if data is None and cache_path and cache_path.is_file():
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        meta["fromCache"] = True
        log.info("Loaded KEV from cache %s", cache_path)

    if data:
        meta["catalogVersion"] = data.get("catalogVersion")
        meta["dateReleased"] = data.get("dateReleased")
        meta["count"] = len(data.get("vulnerabilities") or [])
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
            cve = normalize_cve(row.get("cveID") or "")
            if cve:
                ids.add(cve)
        meta["count"] = len(ids)
    entries = normalize_kev_entries(data, cve_to_rules=cve_to_rules)
    return ids, meta, entries


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

    if not cves:
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
        "status": "mapped",
        "cves": cves,
        "inKev": any_kev,
        "attack": [],
        "references": [],
        "iocs": [],
        "disclaimer": (
            "Public CVE/KEV context only. Not a vulnerability scan result "
            "and not a STIG finding determination."
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
