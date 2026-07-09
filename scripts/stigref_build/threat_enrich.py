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


def load_kev_ids(
    cache_path: Path | None = None,
    *,
    fetch: bool = True,
    timeout: int = 60,
) -> tuple[set[str], dict[str, Any]]:
    """
    Load set of CVE IDs in CISA KEV.
    Prefers cache_path if present; optionally refreshes from CISA.
    """
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
                    json.dumps(data, indent=2), encoding="utf-8"
                )
            log.info("Downloaded CISA KEV catalog")
        except Exception as exc:  # noqa: BLE001
            log.warning("KEV download failed: %s", exc)

    if data is None and cache_path and cache_path.is_file():
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        meta["fromCache"] = True
        log.info("Loaded KEV from cache %s", cache_path)

    ids: set[str] = set()
    if data:
        for row in data.get("vulnerabilities") or []:
            cve = normalize_cve(row.get("cveID") or "")
            if cve:
                ids.add(cve)
        meta["count"] = len(ids)
        meta["catalogVersion"] = data.get("catalogVersion")
        meta["dateReleased"] = data.get("dateReleased")
    return ids, meta


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
