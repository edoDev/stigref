"""Write stigref static data/ tree from parsed STIG dicts."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stigref_build import __version__
from stigref_build.ids import rule_path_id
from stigref_build.disa_packages import (
    annotate_stig,
    build_package_bundle,
    rule_manual_hint,
)
from stigref_build.package_enrich import attach_package_enrichment
from stigref_build.intune_suggest import attach_intune_to_stigs, load_csp_catalog
from stigref_build.tags import build_quick_links, enrich_stig, load_curated
from stigref_build.threat_enrich import (
    attach_threat_to_rules,
    load_kev_bundle,
    normalize_cve,
)
from stigref_build.cis_enrich import attach_cis_to_rules
from stigref_build.scap_enrich import attach_scap_to_rules
from stigref_build.search_index import write_search_index

log = logging.getLogger(__name__)

SEARCH_BODY_MAX = 400


def _sha256_file(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _update_releases_registry(
    out: Path,
    release_info: dict[str, Any],
    *,
    storage: str,
) -> None:
    """
    Maintain data/releases/index.json (or out/releases when out is a release tree).

    When writing the live catalog (storage=live), registry lives at out/releases/index.json.
    When writing into data/releases/YYYY-MM, registry is at parent releases/index.json.
    """
    out = Path(out)
    if storage == "live":
        reg_dir = out / "releases"
    else:
        # out is .../data/releases/2026-07 → registry at .../data/releases
        reg_dir = out.parent if out.parent.name == "releases" else out / "releases"
    reg_dir.mkdir(parents=True, exist_ok=True)
    reg_path = reg_dir / "index.json"
    reg: dict[str, Any] = {"releases": [], "currentRelease": release_info.get("id")}
    if reg_path.is_file():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    releases = list(reg.get("releases") or [])
    # upsert by id
    releases = [r for r in releases if r.get("id") != release_info.get("id")]
    releases.insert(0, release_info)
    reg["releases"] = releases
    if storage == "live":
        reg["currentRelease"] = release_info.get("id")
    _write_json(reg_path, reg)
    # slim per-release pointer (not a full catalog copy)
    if storage == "live":
        slim = reg_dir / str(release_info.get("id") or "unknown")
        slim.mkdir(parents=True, exist_ok=True)
        _write_json(
            slim / "pointer.json",
            {
                **release_info,
                "note": (
                    "Catalog files currently live at data/ root (storage=live). "
                    "On the next import, archive by promoting prior tree or using "
                    "GitHub Release assets — see docs/VERSION_HISTORY.md."
                ),
            },
        )


def measure_data_sizes(out: Path) -> dict[str, Any]:
    """
    Uncompressed size inventory for DESIGN §7.2 budget tracking.
    Does not gzip-compress; reports raw bytes and file counts.
    """
    out = Path(out)
    buckets = {
        "rules": out / "rules",
        "stigs": out / "stigs",
        "search": out / "search",
        "threat": out / "threat",
        "intune": out / "intune",
        "tags": out / "tags",
        "families": out / "families",
    }
    by_area: dict[str, dict[str, int]] = {}
    total_bytes = 0
    total_files = 0
    for name, path in buckets.items():
        b = 0
        n = 0
        if path.is_dir():
            for f in path.rglob("*"):
                if f.is_file():
                    n += 1
                    b += f.stat().st_size
        elif path.is_file():
            n = 1
            b = path.stat().st_size
        by_area[name] = {"bytes": b, "files": n}
        total_bytes += b
        total_files += n
    # top-level meta.json etc.
    other = 0
    if out.is_dir():
        for f in out.iterdir():
            if f.is_file():
                other += f.stat().st_size
                total_files += 1
                total_bytes += f.stat().st_size
    by_area["rootFiles"] = {"bytes": other, "files": sum(1 for f in out.iterdir() if f.is_file()) if out.is_dir() else 0}
    return {
        "totalBytes": total_bytes,
        "totalFiles": total_files,
        "totalMB": round(total_bytes / (1024 * 1024), 2),
        "byArea": by_area,
        "note": "Uncompressed on-disk sizes. DESIGN §7.2 gzip budget is separate (transfer).",
    }


def _truncate(text: str, max_len: int = SEARCH_BODY_MAX) -> str:
    text = " ".join((text or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def merge_rules_across_stigs(stigs: list[dict]) -> dict[str, dict]:
    """
    Index rules by full_rule_id. If the same rule appears in multiple STIGs,
    merge stig_ids lists.
    """
    by_id: dict[str, dict] = {}
    for stig in stigs:
        for rule in stig.get("rules") or []:
            rid = rule["full_rule_id"]
            if rid not in by_id:
                # Shallow copy so we can mutate stig_ids
                item = dict(rule)
                item["stig_ids"] = list(rule.get("stig_ids") or [stig["id"]])
                item["stigs"] = [
                    {
                        "id": stig["id"],
                        "name": stig["name"],
                        "version": stig["version"],
                        "release": stig["release"],
                    }
                ]
                by_id[rid] = item
            else:
                existing = by_id[rid]
                if stig["id"] not in existing["stig_ids"]:
                    existing["stig_ids"].append(stig["id"])
                    existing["stigs"].append(
                        {
                            "id": stig["id"],
                            "name": stig["name"],
                            "version": stig["version"],
                            "release": stig["release"],
                        }
                    )
    return by_id


def build_search_documents(
    stigs: list[dict], rules_by_id: dict[str, dict]
) -> list[dict]:
    docs: list[dict] = []
    for stig in stigs:
        docs.append(
            {
                "id": f"stig:{stig['id']}",
                "type": "stig",
                "title": stig["name"],
                "body": _truncate(
                    " ".join(
                        [
                            stig["name"],
                            stig.get("description") or "",
                            f"V{stig['version']}R{stig['release']}",
                            stig.get("vendor") or "",
                            " ".join(stig.get("roles") or []),
                            " ".join(stig.get("tags") or []),
                        ]
                    )
                ),
                "route": f"/stigs/{stig['id']}",
                "version": stig["version"],
                "release": stig["release"],
                "release_date": stig.get("release_date") or "",
                "vendor": stig.get("vendor") or "",
                "roles": stig.get("roles") or [],
                "tags": stig.get("tags") or [],
                "severity": "",
                "hasIntune": False,
                "hasCve": False,
                "inKev": False,
                "hasAttack": False,
                "hasCis": False,
                "hasOval": False,
                "hasScap": False,
            }
        )

    for rule in rules_by_id.values():
        cves = rule.get("cves") or []
        threat = rule.get("threat") or {}
        intune = rule.get("intune") or {}
        has_intune = bool(
            intune.get("status") == "mapped"
            and (intune.get("suggestions") or [])
        )
        in_kev = bool(threat.get("inKev"))
        has_cve = bool(cves) or bool(threat.get("cves"))
        body = _truncate(
            " ".join(
                [
                    rule.get("full_rule_id") or "",
                    rule.get("title") or "",
                    rule.get("check") or "",
                    rule.get("group_id") or "",
                    " ".join(rule.get("ccis") or []),
                    " ".join(cves),
                ]
            )
        )
        # vendor from first linked stig if present
        vendor = ""
        roles: list[str] = []
        for s in rule.get("stigs") or []:
            # stigs list may only have id/name/version — look up later if needed
            pass
        docs.append(
            {
                "id": f"rule:{rule['full_rule_id']}",
                "type": "rule",
                "title": rule.get("title") or rule["full_rule_id"],
                "body": body,
                "route": f"/rules/{rule_path_id(rule['full_rule_id'])}",
                "severity": rule.get("severity") or "",
                "full_rule_id": rule["full_rule_id"],
                "group_id": rule.get("group_id") or "",
                "ccis": rule.get("ccis") or [],
                "cves": cves,
                "stig_names": [s["name"] for s in rule.get("stigs") or []],
                "vendor": vendor,
                "roles": roles,
                "hasIntune": has_intune,
                "hasCve": has_cve,
                "inKev": in_kev,
                "hasAttack": bool(threat.get("attack")),
                "hasCis": bool(
                    (rule.get("cis") or {}).get("status") == "mapped"
                    and (rule.get("cis") or {}).get("items")
                ),
                "hasOval": bool((rule.get("scap") or {}).get("hasOval")),
                "hasScap": bool((rule.get("scap") or {}).get("hasScapSignal")),
            }
        )
    return docs


def _infer_release_id(source_filename: str | None, explicit: str | None) -> str:
    """Prefer --release; else parse U_SRG-STIG_Library_April_2026.zip → 2026-04."""
    if explicit:
        return explicit.strip()
    name = source_filename or ""
    m = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)[_\s-]?(\d{4})",
        name,
        re.I,
    )
    if m:
        months = {
            "january": "01",
            "february": "02",
            "march": "03",
            "april": "04",
            "may": "05",
            "june": "06",
            "july": "07",
            "august": "08",
            "september": "09",
            "october": "10",
            "november": "11",
            "december": "12",
        }
        mon = months[m.group(1).lower()]
        return f"{m.group(2)}-{mon}"
    # fallback: calendar quarter of today
    now = datetime.now(timezone.utc)
    return f"{now.year}-{now.month:02d}"


def _release_label(release_id: str) -> str:
    try:
        y, m = release_id.split("-", 1)
        months = [
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        return f"{months[int(m)]} {y}"
    except (ValueError, IndexError):
        return release_id


def write_data_tree(
    stigs: list[dict],
    out_dir: str | Path,
    *,
    source_path: Path | None = None,
    source_filename: str | None = None,
    clean: bool = True,
    errors: list[dict] | None = None,
    release_id: str | None = None,
    release_label: str | None = None,
    storage: str = "live",
) -> dict[str, Any]:
    """
    Write the full data/ layout. Returns the meta dict written.

    B-021: ``release_id`` tags this build (e.g. 2026-04). Live catalog uses
    ``storage="live"`` (files at data/ root). Historical trees use
    ``data/releases/{id}/`` with storage relative path.
    """
    out = Path(out_dir)
    if clean and out.exists():
        # Only remove known subtrees to avoid deleting unrelated files
        for sub in (
            "stigs",
            "rules",
            "search",
            "controls",
            "ccis",
            "tags",
            "families",
            "intune",
            "csp",
            "threat",
            "packages",
            "cis",
        ):
            p = out / sub
            if p.exists():
                shutil.rmtree(p)
        meta_path = out / "meta.json"
        if meta_path.exists():
            meta_path.unlink()

    out.mkdir(parents=True, exist_ok=True)

    curated = load_curated()
    stigs = [enrich_stig(s, curated) for s in stigs]

    # DISA GPO + Intune companion packages (quarterly, from raw/)
    repo_root = Path(__file__).resolve().parents[2]
    package_bundle = build_package_bundle(repo_root / "raw")
    stigs = [annotate_stig(s, package_bundle) for s in stigs]

    # Intune CSP suggestions (quick-link products) during STIG processing
    csp_catalog = load_csp_catalog()
    stigs, intune_exports = attach_intune_to_stigs(stigs, catalog=csp_catalog)
    rules_by_id = merge_rules_across_stigs(stigs)

    # Rule-level manual vs policy-amenable hints
    for rule in rules_by_id.values():
        rule["checkAutomation"] = rule_manual_hint(rule)

    # Deep package enrichment: CKL maps, deviations, Settings Catalog, ADMX
    package_enrichment_index = attach_package_enrichment(
        rules_by_id, repo_root / "raw"
    )

    # Threat intel: CVE display + CISA KEV join + full KEV catalog for /kev
    kev_cache = repo_root / "raw" / "intel" / "kev.json"
    # First pass without rule links; second normalize after threat attach
    kev_ids, kev_meta, _ = load_kev_bundle(kev_cache, fetch=True)
    threat_stats = attach_threat_to_rules(rules_by_id, kev_ids)

    # CIS Benchmark crosswalk (mapping-only YAML)
    cis_stats = attach_cis_to_rules(rules_by_id)

    # SCAP/OVAL presence signals (B-050)
    scap_stats = attach_scap_to_rules(rules_by_id)

    cve_to_rules: dict[str, list[str]] = {}
    for rid, rule in rules_by_id.items():
        for cve_row in (rule.get("threat") or {}).get("cves") or []:
            cve = normalize_cve(cve_row.get("id") or "")
            if not cve:
                continue
            cve_to_rules.setdefault(cve, []).append(rid)
        for cve_raw in rule.get("cves") or []:
            cve = normalize_cve(cve_raw)
            if cve:
                cve_to_rules.setdefault(cve, []).append(rid)
    for cve, rids in cve_to_rules.items():
        cve_to_rules[cve] = sorted(set(rids))

    # Rebuild KEV entries with linked STIG rules (from cache, no re-fetch)
    _, kev_meta2, kev_entries = load_kev_bundle(
        kev_cache, fetch=False, cve_to_rules=cve_to_rules
    )
    if kev_meta2.get("count"):
        kev_meta = {**kev_meta, **{k: v for k, v in kev_meta2.items() if v}}

    # Propagate vendor/roles onto rule search docs via stig lookup
    stig_by_id = {s["id"]: s for s in stigs}

    # STIG index + detail (detail includes rule summaries, not always full text)
    stig_index: list[dict] = []
    for stig in sorted(
        stigs, key=lambda s: (s.get("release_date") or "", s["name"]), reverse=True
    ):
        summaries = [
            {
                "id": r["full_rule_id"],
                "full_rule_id": r["full_rule_id"],
                "title": r.get("title") or "",
                "severity": r.get("severity") or "",
                "group_id": r.get("group_id") or "",
            }
            for r in stig.get("rules") or []
        ]
        detail = {
            "id": stig["id"],
            "name": stig["name"],
            "description": stig.get("description") or "",
            "version": stig["version"],
            "release": stig["release"],
            "release_date": stig.get("release_date") or "",
            "rule_count": len(summaries),
            "rules": summaries,
            "source": stig.get("source") or "",
            "family": stig.get("family") or "",
            "vendor": stig.get("vendor") or "",
            "roles": stig.get("roles") or [],
            "tags": stig.get("tags") or [],
            "quicklink_id": stig.get("quicklink_id"),
            "automation": stig.get("automation") or {},
        }
        _write_json(out / "stigs" / "by-id" / f"{stig['id']}.json", detail)
        auto = stig.get("automation") or {}
        stig_index.append(
            {
                "id": stig["id"],
                "name": stig["name"],
                "version": stig["version"],
                "release": stig["release"],
                "release_date": stig.get("release_date") or "",
                "rule_count": len(summaries),
                "family": stig.get("family") or "",
                "vendor": stig.get("vendor") or "",
                "roles": stig.get("roles") or [],
                "tags": stig.get("tags") or [],
                "quicklink_id": stig.get("quicklink_id"),
                "hasGpoPackage": bool(auto.get("hasGpoPackage")),
                "hasIntunePackage": bool(auto.get("hasIntunePackage")),
                "shbRelated": bool(auto.get("shbRelated")),
                "manualOrPlatformNative": bool(auto.get("manualOrPlatformNative")),
            }
        )

    _write_json(out / "stigs" / "index.json", {"stigs": stig_index, "total": len(stig_index)})

    # Facets + quick links for UI filters
    vendors = sorted({s["vendor"] for s in stig_index if s.get("vendor")})
    roles = sorted({r for s in stig_index for r in (s.get("roles") or [])})
    tag_set = sorted({t for s in stig_index for t in (s.get("tags") or [])})
    quick_links = build_quick_links(stigs, curated)
    _write_json(
        out / "tags" / "catalog.json",
        {
            "vendors": vendors,
            "roles": roles,
            "tags": tag_set,
            "quickLinks": quick_links,
            "filterHints": {
                "roles": ["server", "workstation", "browser", "mobile", "database", "network", "cloud", "application", "other"],
                "special": [
                    {"id": "intune", "label": "Intune-related", "tag": "intune"},
                    {"id": "intune-companion", "label": "Intune companion", "tag": "intune-companion"},
                    {"id": "gpo-companion", "label": "GPO companion", "tag": "gpo-companion"},
                    {"id": "has-gpo-package", "label": "DISA GPO package", "tag": "has-gpo-package"},
                    {"id": "has-intune-package", "label": "DISA Intune package", "tag": "has-intune-package"},
                    {"id": "no-disa-automation-package", "label": "No DISA GPO/Intune package", "tag": "no-disa-automation-package"},
                    {"id": "manual-or-platform-native", "label": "Manual / platform-native", "tag": "manual-or-platform-native"},
                    {"id": "shb-related", "label": "SHB-related host stack", "tag": "shb-related"},
                ],
            },
        },
    )

    # Family map (foundation for multi-release history)
    families: dict[str, list[dict]] = {}
    for s in stig_index:
        fam = s.get("family") or "unknown"
        families.setdefault(fam, []).append(
            {
                "id": s["id"],
                "name": s["name"],
                "version": s["version"],
                "release": s["release"],
                "release_date": s.get("release_date") or "",
            }
        )
    _write_json(
        out / "families" / "index.json",
        {
            "families": [
                {"family": k, "versions": v, "count": len(v)}
                for k, v in sorted(families.items(), key=lambda kv: kv[0])
            ],
            "total": len(families),
        },
    )

    # Full rule detail files
    for rid, rule in rules_by_id.items():
        path_id = rule_path_id(rid)
        detail = {
            "id": rid,
            "full_rule_id": rid,
            "rule_id": rule.get("rule_id") or "",
            "rule_revision": rule.get("rule_revision") or "",
            "group_id": rule.get("group_id") or "",
            "group_title": rule.get("group_title") or "",
            "title": rule.get("title") or "",
            "severity": rule.get("severity") or "",
            "description": rule.get("description") or "",
            "check": rule.get("check") or "",
            "fix": rule.get("fix") or "",
            "ccis": rule.get("ccis") or [],
            "cves": rule.get("cves") or [],
            "metadata": rule.get("metadata") or {},
            "stigs": rule.get("stigs") or [],
            "stig_ids": rule.get("stig_ids") or [],
            "intune": rule.get("intune"),
            "threat": rule.get("threat"),
            "cis": rule.get("cis"),
            "scap": rule.get("scap"),
            "checkAutomation": rule.get("checkAutomation"),
            "packageEnrichment": rule.get("packageEnrichment"),
            "enrichmentTags": rule.get("enrichmentTags"),
        }
        _write_json(out / "rules" / "by-id" / f"{path_id}.json", detail)

    # CIS crosswalk index
    cis_index_rules = []
    for rid, rule in sorted(rules_by_id.items()):
        items = (rule.get("cis") or {}).get("items") or []
        if not items:
            continue
        cis_index_rules.append(
            {
                "full_rule_id": rid,
                "title": rule.get("title"),
                "cisCount": len(items),
                "cisIds": [i.get("id") for i in items],
                "profiles": sorted(
                    {i.get("profile") for i in items if i.get("profile")}
                ),
            }
        )
    _write_json(
        out / "cis" / "index.json",
        {
            "totalMappedRules": len(cis_index_rules),
            "mapFiles": cis_stats.get("mapFiles"),
            "disclaimer": (
                "CIS crosswalk is assistive mapping only. Official CIS Benchmark "
                "documents are authoritative."
            ),
            "rules": cis_index_rules,
        },
    )

    # Companion package index (GPO + Intune) for docs/UI
    _write_json(
        out / "packages" / "index.json",
        {
            "paths": package_bundle.get("paths"),
            "gpo": package_bundle.get("gpo"),
            "intune": {
                "filename": (package_bundle.get("intune") or {}).get("filename"),
                "type": "intune",
                "profileCount": (package_bundle.get("intune") or {}).get("profileCount"),
                "notes": (package_bundle.get("intune") or {}).get("notes"),
                "profiles": [
                    {
                        "name": p.get("name"),
                        "category": p.get("category"),
                        "path": p.get("path"),
                    }
                    for p in ((package_bundle.get("intune") or {}).get("profiles") or [])
                ],
            }
            if package_bundle.get("intune")
            else None,
            "enrichment": package_enrichment_index,
            "stats": {
                "stigsWithGpo": sum(1 for s in stig_index if s.get("hasGpoPackage")),
                "stigsWithIntune": sum(1 for s in stig_index if s.get("hasIntunePackage")),
                "stigsShbRelated": sum(1 for s in stig_index if s.get("shbRelated")),
                "stigsManualOrPlatform": sum(
                    1 for s in stig_index if s.get("manualOrPlatformNative")
                ),
                **(package_enrichment_index.get("stats") or {}),
            },
            "shbNote": (
                "shb-related tags mark STIGs commonly stacked in DoD Secure Host Baseline "
                "style Windows host hardening (Win10/11 + Edge/Chrome + Defender + Firewall + "
                "Office/Reader). Not an official SHB product matrix."
            ),
        },
    )

    # Threat meta + full KEV catalog for dedicated browser page
    _write_json(
        out / "threat" / "meta.json",
        {
            "kev": kev_meta,
            "stats": threat_stats,
            "disclaimer": (
                "Public CVE/KEV context only. Not a vulnerability scan result."
            ),
        },
    )
    _write_json(
        out / "threat" / "kev.json",
        {
            "catalogVersion": kev_meta.get("catalogVersion"),
            "dateReleased": kev_meta.get("dateReleased"),
            "fetchedAt": kev_meta.get("fetchedAt"),
            "source": kev_meta.get("source"),
            "catalogUrl": kev_meta.get("catalogUrl"),
            "count": len(kev_entries),
            "linkedToStigCount": sum(
                1 for e in kev_entries if e.get("linkedRules")
            ),
            "vulnerabilities": kev_entries,
            "disclaimer": (
                "CISA Known Exploited Vulnerabilities catalog. "
                "stigref hosts a snapshot for search; always confirm on cisa.gov."
            ),
        },
    )

    # CSP catalog snapshot + product-level Intune export packages
    _write_json(
        out / "csp" / "catalog.json",
        {
            "version": csp_catalog.get("version"),
            "sourceNote": csp_catalog.get("sourceNote"),
            "learnPolicyIndex": csp_catalog.get("learnPolicyIndex"),
            "entries": csp_catalog.get("entries") or [],
            "count": len(csp_catalog.get("entries") or []),
        },
    )
    for exp in intune_exports:
        product = exp.get("product") or "unknown"
        _write_json(out / "intune" / "products" / f"{product}.json", exp)
    _write_json(
        out / "intune" / "index.json",
        {
            "products": [
                {
                    "product": e.get("product"),
                    "stigId": (e.get("stig") or {}).get("id"),
                    "stigName": (e.get("stig") or {}).get("name"),
                    "settings": (e.get("counts") or {}).get("settings"),
                    "mappedRules": (e.get("counts") or {}).get("mappedRules"),
                    "rules": (e.get("counts") or {}).get("rules"),
                    "path": f"intune/products/{e.get('product')}.json",
                }
                for e in intune_exports
            ],
            "total": len(intune_exports),
        },
    )

    # Attach vendor from first linked STIG onto rules for search facets
    for rule in rules_by_id.values():
        for link in rule.get("stigs") or []:
            sid = link.get("id")
            parent = stig_by_id.get(sid) if sid else None
            if parent:
                rule["_search_vendor"] = parent.get("vendor") or ""
                rule["_search_roles"] = parent.get("roles") or []
                break

    docs = build_search_documents(stigs, rules_by_id)
    # fill vendor/roles on rule docs from temporary fields
    for doc in docs:
        if doc.get("type") != "rule":
            continue
        rid = doc.get("full_rule_id")
        rule = rules_by_id.get(rid) if rid else None
        if rule:
            doc["vendor"] = rule.get("_search_vendor") or ""
            doc["roles"] = rule.get("_search_roles") or []

    # B-041: sharded + gzip search index (no monolithic documents.json by default)
    write_search_index(out / "search", docs, write_legacy_monolith=False)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    # Prefer newest STIG release_date as content lastUpdated when available
    dates = [s.get("release_date") for s in stigs if s.get("release_date")]
    content_updated = max(dates) if dates else now[:10]

    src_name = source_filename
    if src_name is None and source_path is not None:
        src_name = source_path.name

    rid = _infer_release_id(src_name, release_id)
    rlabel = release_label or _release_label(rid)
    release_info = {
        "id": rid,
        "label": rlabel,
        "sourceFile": src_name,
        "builtAt": now,
        "storage": storage,
    }

    meta = {
        "lastUpdated": content_updated
        if "T" in str(content_updated)
        else f"{content_updated}T00:00:00Z"
        if len(str(content_updated)) == 10
        else now,
        "builtAt": now,
        "currentRelease": rid,
        "release": release_info,
        "releases": [release_info],
        "source": {
            "filename": src_name,
            "sha256": _sha256_file(source_path) if source_path else None,
            "urlHint": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/",
        },
        "counts": {
            "stigs": len(stigs),
            "rules": len(rules_by_id),
            "rulesWithCve": threat_stats.get("rulesWithCve", 0),
            "rulesWithKev": threat_stats.get("rulesWithKev", 0),
            "rulesWithCis": cis_stats.get("rulesWithCis", 0),
            "rulesWithOval": scap_stats.get("rulesWithOval", 0),
            "rulesWithScapSignal": scap_stats.get("rulesWithScapSignal", 0),
            "controls": 0,
            "ccis": 0,
            "searchDocuments": len(docs),
        },
        "parseErrors": len(errors or []),
        "generator": f"stigref-build {__version__}",
    }
    if errors:
        meta["errors"] = errors[:50]  # cap noise in meta

    # Size inventory (B-076) — write after payloads so counts are accurate
    _write_json(out / "meta.json", meta)
    try:
        meta["sizes"] = measure_data_sizes(out)
        # Re-write including sizes (meta itself is tiny)
        _write_json(out / "meta.json", meta)
    except OSError as exc:
        log.error("Could not measure data sizes: %s", exc)

    # B-021: register this release under data/releases/index.json when writing live tree
    try:
        _update_releases_registry(out, release_info, storage=storage)
    except OSError as exc:
        log.error("Could not update releases registry: %s", exc)
    log.info(
        "Wrote data to %s (%s stigs, %s rules, %s search docs)",
        out,
        meta["counts"]["stigs"],
        meta["counts"]["rules"],
        meta["counts"]["searchDocuments"],
    )
    return meta
