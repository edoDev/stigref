"""Precompute Library Observatory / Insights stats (B-090).

Produces ``data/stats/insights.json`` for the static ``/insights`` page.
Callable from write_data (in-memory) or build_insights.py (from disk).
"""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

log = logging.getLogger(__name__)

FORMAT = "stigref-insights/v1"
DISCLAIMERS = {
    "general": (
        "Observatory metrics are derived from public STIG/XCCDF and curated maps. "
        "Not a compliance score, vulnerability assessment, or official DoD product."
    ),
    "kev": (
        "KEV is a standalone CISA catalog. Per-rule KEV intersection is often near-zero "
        "because public XCCDF rarely embeds CVEs."
    ),
    "attack": (
        "ATT&CK links are keyword/seed suggestions with low confidence — not authoritative mappings."
    ),
    "cis": (
        "CIS crosswalk is assistive mapping only. Official CIS Benchmark documents are authoritative."
    ),
    "intune": (
        "Intune coverage is map-assisted, not a guarantee a setting exists in Settings Catalog "
        "or that the OMA-URI fully satisfies the STIG check."
    ),
}


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sev_key(raw: Any) -> str:
    s = (str(raw or "")).strip().lower()
    if s in ("high", "cat i", "cati", "i"):
        return "high"
    if s in ("medium", "cat ii", "catii", "ii", "moderate"):
        return "medium"
    if s in ("low", "cat iii", "catiii", "iii"):
        return "low"
    return "unknown"


def _pct(n: int, d: int) -> float:
    if not d:
        return 0.0
    return round(100.0 * n / d, 1)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_rule_files(rules_dir: Path) -> Iterable[Path]:
    by_id = rules_dir / "by-id"
    if not by_id.is_dir():
        return
    yield from by_id.glob("*.json")


def build_insights_from_memory(
    stigs: list[dict[str, Any]],
    rules_by_id: dict[str, dict[str, Any]],
    *,
    intune_index: dict[str, Any] | None = None,
    kev_payload: dict[str, Any] | None = None,
    cis_index: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
    search_manifest: dict[str, Any] | None = None,
    product_extras: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build insights document from in-memory pipeline objects.

    Accepts full rule dicts (with intune/threat/cis) or already-thinned rows.
    """
    rules: list[dict[str, Any]] = []
    for r in rules_by_id.values():
        if "has_intune" in r or "check_style" in r:
            rules.append(r)
        else:
            rules.append(_thin_rule(r))
    return _assemble(
        stigs=stigs,
        rules=rules,
        intune_index=intune_index or {},
        kev_payload=kev_payload or {},
        cis_index=cis_index or {},
        meta=meta or {},
        search_manifest=search_manifest or {},
        product_extras=product_extras,
    )


def build_insights_from_disk(data_dir: str | Path) -> dict[str, Any]:
    """Build insights by scanning an existing data/ tree (no full STIG reparse)."""
    data = Path(data_dir)
    stig_index = _read_json(data / "stigs" / "index.json")
    stigs_meta = stig_index.get("stigs") if isinstance(stig_index, dict) else stig_index
    if not isinstance(stigs_meta, list):
        stigs_meta = []

    # Lightweight rule scan — only fields needed for aggregates
    rules: list[dict[str, Any]] = []
    rules_dir = data / "rules"
    n = 0
    for path in _iter_rule_files(rules_dir):
        try:
            raw = _read_json(path)
        except (OSError, json.JSONDecodeError, UnicodeError) as exc:
            log.error("Skip rule %s: %s", path.name, exc)
            continue
        rules.append(_thin_rule(raw))
        n += 1
        if n % 5000 == 0:
            log.info("Scanned %s rules…", n)
    log.info("Scanned %s rules for insights", n)

    intune_index: dict[str, Any] = {}
    ip = data / "intune" / "index.json"
    if ip.is_file():
        intune_index = _read_json(ip)

    # Enrich intune products with severity coverage + unmapped CAT I from rule scan
    stig_rules: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rules:
        for sid in r.get("stig_ids") or []:
            stig_rules[sid].append(r)

    products = list(intune_index.get("products") or [])
    # Load product packs for confidence / kind mix
    for p in products:
        product_id = p.get("product")
        pack_path = data / "intune" / "products" / f"{product_id}.json"
        pack: dict[str, Any] = {}
        if pack_path.is_file():
            try:
                pack = _read_json(pack_path)
            except (OSError, json.JSONDecodeError):
                pack = {}
        p["_pack"] = pack
        p["_rules"] = stig_rules.get(p.get("stigId") or "", [])

    kev_payload: dict[str, Any] = {}
    kp = data / "threat" / "kev.json"
    if kp.is_file():
        kev_payload = _read_json(kp)

    cis_index: dict[str, Any] = {}
    cp = data / "cis" / "index.json"
    if cp.is_file():
        cis_index = _read_json(cp)

    meta: dict[str, Any] = {}
    mp = data / "meta.json"
    if mp.is_file():
        meta = _read_json(mp)

    search_manifest: dict[str, Any] = {}
    sm = data / "search" / "manifest.json"
    if sm.is_file():
        search_manifest = _read_json(sm)

    doc = _assemble(
        stigs=stigs_meta,
        rules=rules,
        intune_index=intune_index,
        kev_payload=kev_payload,
        cis_index=cis_index,
        meta=meta,
        search_manifest=search_manifest,
        product_extras=products,
    )
    return doc


def _thin_rule(raw: dict[str, Any]) -> dict[str, Any]:
    threat = raw.get("threat") or {}
    scap = raw.get("scap") or {}
    intune = raw.get("intune") or {}
    cis = raw.get("cis") or {}
    pe = raw.get("packageEnrichment") or {}
    sugs = intune.get("suggestions") or []
    confs = [str(s.get("confidence") or "unknown").lower() for s in sugs]
    kinds = [str(s.get("kind") or "unknown").lower() for s in sugs]
    return {
        "full_rule_id": raw.get("full_rule_id") or raw.get("id"),
        "title": raw.get("title") or "",
        "severity": raw.get("severity"),
        "ccis": list(raw.get("ccis") or []),
        "stig_ids": list(raw.get("stig_ids") or []),
        "has_intune": bool(sugs),
        "intune_confidences": confs,
        "intune_kinds": kinds,
        "in_kev": bool(threat.get("inKev")),
        "has_cve": bool(threat.get("cves") or raw.get("cves")),
        "attack": list(threat.get("attack") or []),
        "has_cis": (cis.get("status") == "mapped") or bool(cis.get("items")),
        "cis_ids": [i.get("id") for i in (cis.get("items") or []) if i.get("id")],
        "cis_products": [
            i.get("product") for i in (cis.get("items") or []) if i.get("product")
        ],
        "has_oval": bool(scap.get("hasOval")),
        "has_scap": bool(scap.get("hasScapSignal") or scap.get("hasOval")),
        "has_ckl": bool(pe.get("ckl")),
        "has_deviation": bool(pe.get("deviation")),
        "check_style": (raw.get("checkAutomation") or {}).get("checkStyle")
        or "unspecified",
    }


def _assemble(
    *,
    stigs: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    intune_index: dict[str, Any],
    kev_payload: dict[str, Any],
    cis_index: dict[str, Any],
    meta: dict[str, Any],
    search_manifest: dict[str, Any],
    product_extras: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    severity = Counter()
    vendors_stigs: Counter[str] = Counter()
    vendors_rules: Counter[str] = Counter()
    roles_stigs: Counter[str] = Counter()
    roles_rules: Counter[str] = Counter()
    family_rows: dict[str, dict[str, Any]] = {}

    auto_stigs = {
        "gpoPackage": 0,
        "intunePackage": 0,
        "both": 0,
        "neither": 0,
        "shb": 0,
        "manualOrPlatform": 0,
    }

    for s in stigs:
        vendor = s.get("vendor") or "Unknown"
        family = s.get("family") or s.get("id") or "unknown"
        rc = int(s.get("rule_count") or 0)
        vendors_stigs[vendor] += 1
        vendors_rules[vendor] += rc
        for role in s.get("roles") or ["other"]:
            roles_stigs[str(role)] += 1
            roles_rules[str(role)] += rc

        gpo = bool(s.get("hasGpoPackage"))
        iun = bool(s.get("hasIntunePackage"))
        if gpo and iun:
            auto_stigs["both"] += 1
        elif gpo:
            auto_stigs["gpoPackage"] += 1
        elif iun:
            auto_stigs["intunePackage"] += 1
        else:
            auto_stigs["neither"] += 1
        if s.get("shbRelated"):
            auto_stigs["shb"] += 1
        if s.get("manualOrPlatformNative"):
            auto_stigs["manualOrPlatform"] += 1

        key = f"{vendor}::{family}"
        row = family_rows.get(key)
        if not row:
            row = {
                "vendor": vendor,
                "family": family,
                "stigs": 0,
                "rules": 0,
                "hasGpo": False,
                "hasIntunePackage": False,
                "shbRelated": False,
            }
            family_rows[key] = row
        row["stigs"] += 1
        row["rules"] += rc
        row["hasGpo"] = row["hasGpo"] or gpo
        row["hasIntunePackage"] = row["hasIntunePackage"] or iun
        row["shbRelated"] = row["shbRelated"] or bool(s.get("shbRelated"))

    cci_counter: Counter[str] = Counter()
    attack_counter: Counter[str] = Counter()
    attack_names: dict[str, str] = {}
    cis_id_counter: Counter[str] = Counter()
    check_styles: Counter[str] = Counter()
    rule_auto = {
        "withIntuneSuggestion": 0,
        "withScapSignal": 0,
        "withOval": 0,
        "withCkl": 0,
        "withDeviation": 0,
        "withCis": 0,
        "withCve": 0,
        "withKev": 0,
        "withAttack": 0,
        "withCci": 0,
    }

    for r in rules:
        severity[_sev_key(r.get("severity"))] += 1
        if r.get("has_intune"):
            rule_auto["withIntuneSuggestion"] += 1
        if r.get("has_scap"):
            rule_auto["withScapSignal"] += 1
        if r.get("has_oval"):
            rule_auto["withOval"] += 1
        if r.get("has_ckl"):
            rule_auto["withCkl"] += 1
        if r.get("has_deviation"):
            rule_auto["withDeviation"] += 1
        if r.get("has_cis"):
            rule_auto["withCis"] += 1
        if r.get("has_cve"):
            rule_auto["withCve"] += 1
        if r.get("in_kev"):
            rule_auto["withKev"] += 1
        attacks = r.get("attack") or []
        if attacks:
            rule_auto["withAttack"] += 1
            for a in attacks:
                tid = a.get("techniqueId") or a.get("id") or "?"
                attack_counter[tid] += 1
                if a.get("name"):
                    attack_names[tid] = a["name"]
        ccis = r.get("ccis") or []
        if ccis:
            rule_auto["withCci"] += 1
            for c in ccis:
                cci_counter[str(c)] += 1
        for cid in r.get("cis_ids") or []:
            cis_id_counter[str(cid)] += 1
        check_styles[str(r.get("check_style") or "unspecified")] += 1

    # Intune product scorecards
    intune_products = _intune_scorecards(
        intune_index, product_extras=product_extras, all_rules=rules
    )

    # CIS summary
    cis_by_product: Counter[str] = Counter()
    for r in rules:
        for prod in r.get("cis_products") or []:
            cis_by_product[str(prod)] += 1
    cis_section = {
        "rulesWithCis": rule_auto["withCis"],
        "totalMappedRules": cis_index.get("totalMappedRules") or rule_auto["withCis"],
        "mapFiles": cis_index.get("mapFiles"),
        "byProduct": [
            {"product": k, "rules": v}
            for k, v in cis_by_product.most_common(30)
        ],
        "topCisIds": [
            {"id": k, "rules": v} for k, v in cis_id_counter.most_common(25)
        ],
        "disclaimer": DISCLAIMERS["cis"],
    }

    # CCI gravity
    cci_section = {
        "uniqueCcis": len(cci_counter),
        "rulesWithCci": rule_auto["withCci"],
        "top": [
            {"id": k, "ruleCount": v} for k, v in cci_counter.most_common(40)
        ],
    }

    # ATT&CK
    attack_section = {
        "rulesWithAttack": rule_auto["withAttack"],
        "techniques": [
            {
                "id": k,
                "name": attack_names.get(k, ""),
                "ruleCount": v,
            }
            for k, v in attack_counter.most_common(40)
        ],
        "disclaimer": DISCLAIMERS["attack"],
    }

    # KEV observatory
    kev_section = _kev_stats(kev_payload, rule_auto["withKev"])

    # Search transfer size
    totals = (search_manifest or {}).get("totals") or {}
    search_gz = totals.get("bytesGz") or 0

    sizes = (meta or {}).get("sizes") or {}
    counts = (meta or {}).get("counts") or {}

    kpis = {
        "stigs": len(stigs),
        "rules": len(rules),
        "vendors": len(vendors_stigs),
        "families": len(family_rows),
        "stigsWithGpo": sum(1 for s in stigs if s.get("hasGpoPackage")),
        "stigsWithIntunePackage": sum(1 for s in stigs if s.get("hasIntunePackage")),
        "stigsShbRelated": sum(1 for s in stigs if s.get("shbRelated")),
        "rulesWithCve": rule_auto["withCve"],
        "rulesWithKev": rule_auto["withKev"],
        "rulesWithCis": rule_auto["withCis"],
        "rulesWithOval": rule_auto["withOval"],
        "rulesWithScap": rule_auto["withScapSignal"],
        "rulesWithIntuneMap": rule_auto["withIntuneSuggestion"],
        "rulesWithAttack": rule_auto["withAttack"],
        "uniqueCcis": len(cci_counter),
        "intuneProducts": len(intune_products),
        "searchTransferBytesGz": search_gz,
        "searchTransferMBGz": round(search_gz / (1024 * 1024), 2) if search_gz else 0,
        "dataTotalMB": sizes.get("totalMB"),
        "parseErrors": meta.get("parseErrors", 0) if meta else 0,
    }

    landscape = sorted(
        family_rows.values(), key=lambda r: (-int(r["rules"]), r["vendor"], r["family"])
    )[:80]

    scorecards = _family_scorecards(stigs, rules, intune_products)

    vendors = [
        {
            "name": name,
            "stigs": vendors_stigs[name],
            "rules": vendors_rules[name],
        }
        for name, _ in vendors_rules.most_common(40)
    ]
    roles = [
        {
            "role": name,
            "stigs": roles_stigs[name],
            "rules": roles_rules[name],
        }
        for name, _ in roles_rules.most_common(20)
    ]

    health = {
        "builtAt": meta.get("builtAt"),
        "lastUpdated": meta.get("lastUpdated"),
        "currentRelease": meta.get("currentRelease"),
        "sourceFile": (meta.get("source") or {}).get("filename"),
        "sourceSha256": (meta.get("source") or {}).get("sha256"),
        "generator": meta.get("generator"),
        "parseErrors": meta.get("parseErrors", 0),
        "totalMB": sizes.get("totalMB"),
        "totalFiles": sizes.get("totalFiles"),
        "searchBytesGz": search_gz,
        "searchShards": len((search_manifest or {}).get("shards") or []),
        "counts": counts,
    }

    delta = {
        "available": len(meta.get("releases") or []) > 1,
        "note": (
            "Cross-release delta charts unlock when a second DISA library quarter is imported."
            if len(meta.get("releases") or []) <= 1
            else "Multiple releases registered — use Releases page and diff_releases.py for detail."
        ),
        "releases": meta.get("releases") or [],
    }

    return {
        "format": FORMAT,
        "generatedAt": _now(),
        "releaseId": meta.get("currentRelease") or (meta.get("release") or {}).get("id"),
        "disclaimers": DISCLAIMERS,
        "kpis": kpis,
        "severity": {
            "high": severity.get("high", 0),
            "medium": severity.get("medium", 0),
            "low": severity.get("low", 0),
            "unknown": severity.get("unknown", 0),
        },
        "vendors": vendors,
        "roles": roles,
        "landscape": landscape,
        "automation": {
            "stigs": auto_stigs,
            "rules": {**rule_auto, "checkStyle": dict(check_styles)},
        },
        "intuneProducts": intune_products,
        "cis": cis_section,
        "cci": cci_section,
        "attack": attack_section,
        "kev": kev_section,
        "health": health,
        "delta": delta,
        "scorecards": scorecards,
    }


def _intune_scorecards(
    intune_index: dict[str, Any],
    *,
    product_extras: list[dict[str, Any]] | None,
    all_rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    products = product_extras if product_extras is not None else list(
        intune_index.get("products") or []
    )
    # Fallback: group rules by product via cis/intune only if no extras
    out: list[dict[str, Any]] = []
    for p in products:
        product = p.get("product") or "unknown"
        total = int(p.get("rules") or 0)
        mapped = int(p.get("mappedRules") or 0)
        settings = int(p.get("settings") or 0)
        pack = p.get("_pack") or {}
        pack_rules: list[dict[str, Any]] = p.get("_rules") or []

        conf = Counter()
        kinds = Counter()
        for s in pack.get("settings") or []:
            conf[str(s.get("confidence") or "unknown").lower()] += 1
            kinds[str(s.get("kind") or "unknown").lower()] += 1
        # Also from rule suggestions if pack empty
        if not conf and pack_rules:
            for r in pack_rules:
                for c in r.get("intune_confidences") or []:
                    conf[c] += 1
                for k in r.get("intune_kinds") or []:
                    kinds[k] += 1

        sev_total = Counter()
        sev_mapped = Counter()
        unmapped_cat_i: list[dict[str, str]] = []
        mapped_ids = set()
        for s in pack.get("settings") or []:
            for rid in s.get("sourceRules") or []:
                mapped_ids.add(str(rid))
        # pack settings may use SV- ids without full path form
        for r in pack_rules:
            sk = _sev_key(r.get("severity"))
            sev_total[sk] += 1
            rid = r.get("full_rule_id") or ""
            is_mapped = bool(r.get("has_intune")) or rid in mapped_ids
            # partial id match
            if not is_mapped and mapped_ids:
                base = rid.split("r")[0] if rid else ""
                is_mapped = any(
                    m == rid or m.startswith(base) or rid.startswith(m.split("r")[0])
                    for m in mapped_ids
                )
            if is_mapped:
                sev_mapped[sk] += 1
            elif sk == "high" and len(unmapped_cat_i) < 12:
                unmapped_cat_i.append(
                    {
                        "id": rid,
                        "title": (r.get("title") or "")[:140],
                    }
                )

        if not total and pack_rules:
            total = len(pack_rules)
        if not mapped:
            mapped = sum(1 for r in pack_rules if r.get("has_intune")) or mapped

        out.append(
            {
                "product": product,
                "stigId": p.get("stigId"),
                "stigName": p.get("stigName"),
                "rules": total,
                "mappedRules": mapped,
                "settings": settings,
                "coveragePct": _pct(mapped, total),
                "severityCoverage": {
                    "high": {
                        "total": sev_total.get("high", 0),
                        "mapped": sev_mapped.get("high", 0),
                        "pct": _pct(
                            sev_mapped.get("high", 0), sev_total.get("high", 0)
                        ),
                    },
                    "medium": {
                        "total": sev_total.get("medium", 0),
                        "mapped": sev_mapped.get("medium", 0),
                        "pct": _pct(
                            sev_mapped.get("medium", 0), sev_total.get("medium", 0)
                        ),
                    },
                    "low": {
                        "total": sev_total.get("low", 0),
                        "mapped": sev_mapped.get("low", 0),
                        "pct": _pct(
                            sev_mapped.get("low", 0), sev_total.get("low", 0)
                        ),
                    },
                },
                "confidence": {
                    "high": conf.get("high", 0),
                    "medium": conf.get("medium", 0),
                    "low": conf.get("low", 0),
                },
                "kinds": dict(kinds),
                "unmappedCatI": unmapped_cat_i,
            }
        )
    out.sort(key=lambda x: (-x["coveragePct"], x["product"]))
    return out


def _family_scorecards(
    stigs: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    intune_products: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Top product-family scorecards (by rule count)."""
    intune_by_stig = {
        p.get("stigId"): p for p in intune_products if p.get("stigId")
    }
    rules_by_stig: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rules:
        for sid in r.get("stig_ids") or []:
            rules_by_stig[sid].append(r)

    cards: list[dict[str, Any]] = []
    for s in sorted(stigs, key=lambda x: -int(x.get("rule_count") or 0))[:40]:
        sid = s.get("id")
        rs = rules_by_stig.get(sid or "", [])
        sev = Counter(_sev_key(r.get("severity")) for r in rs)
        iun = intune_by_stig.get(sid)
        cards.append(
            {
                "stigId": sid,
                "name": s.get("name"),
                "vendor": s.get("vendor"),
                "family": s.get("family"),
                "ruleCount": int(s.get("rule_count") or len(rs)),
                "severity": {
                    "high": sev.get("high", 0),
                    "medium": sev.get("medium", 0),
                    "low": sev.get("low", 0),
                },
                "hasGpoPackage": bool(s.get("hasGpoPackage")),
                "hasIntunePackage": bool(s.get("hasIntunePackage")),
                "shbRelated": bool(s.get("shbRelated")),
                "intuneCoveragePct": iun.get("coveragePct") if iun else None,
                "intuneProduct": iun.get("product") if iun else None,
                "rulesWithCis": sum(1 for r in rs if r.get("has_cis")),
                "rulesWithScap": sum(1 for r in rs if r.get("has_scap")),
            }
        )
    return cards


def _kev_stats(kev_payload: dict[str, Any], rules_with_kev: int) -> dict[str, Any]:
    vulns = kev_payload.get("vulnerabilities") or kev_payload.get("entries") or []
    by_year: Counter[str] = Counter()
    by_vendor: Counter[str] = Counter()
    ransomware = 0
    for v in vulns:
        da = str(v.get("dateAdded") or "")[:4]
        if da.isdigit():
            by_year[da] += 1
        vendor = v.get("vendorProject") or "Unknown"
        by_vendor[str(vendor)] += 1
        kr = str(v.get("knownRansomwareCampaignUse") or "").lower()
        if kr in ("known", "yes", "true"):
            ransomware += 1

    return {
        "catalogCount": kev_payload.get("count") or len(vulns),
        "catalogVersion": kev_payload.get("catalogVersion"),
        "dateReleased": kev_payload.get("dateReleased"),
        "fetchedAt": kev_payload.get("fetchedAt"),
        "rulesWithKev": rules_with_kev,
        "ransomwareKnown": ransomware,
        "byYear": [
            {"year": y, "count": c} for y, c in sorted(by_year.items())
        ],
        "topVendors": [
            {"vendor": v, "count": c} for v, c in by_vendor.most_common(20)
        ],
        "disclaimer": DISCLAIMERS["kev"],
    }


def write_insights(out_dir: str | Path, doc: dict[str, Any]) -> Path:
    out = Path(out_dir)
    path = out / "stats" / "insights.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info(
        "Wrote insights → %s (kpis stigs=%s rules=%s)",
        path,
        (doc.get("kpis") or {}).get("stigs"),
        (doc.get("kpis") or {}).get("rules"),
    )
    return path
