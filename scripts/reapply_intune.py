#!/usr/bin/env python3
"""
Re-run Intune CSP suggestion stage against existing data/ without re-parsing
the full DISA library ZIP (B-011 iteration helper).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stigref_build.ids import rule_path_id  # noqa: E402
from stigref_build.intune_suggest import (  # noqa: E402
    attach_intune_to_stigs,
    load_all_maps,
    load_csp_catalog,
)
from stigref_build.tags import enrich_stig, load_curated  # noqa: E402
from stigref_build.write_data import _write_json  # noqa: E402

log = logging.getLogger("reapply_intune")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(__file__).resolve().parents[1]
    data = root / "data"
    stigs_idx_path = data / "stigs" / "index.json"
    if not stigs_idx_path.is_file():
        log.error("Missing %s", stigs_idx_path)
        return 1

    idx = json.loads(stigs_idx_path.read_text(encoding="utf-8"))
    stigs_meta = idx.get("stigs") or []
    curated = load_curated()
    maps = load_all_maps()
    catalog = load_csp_catalog()

    stigs: list[dict] = []
    for entry in stigs_meta:
        sid = entry["id"]
        path = data / "stigs" / "by-id" / f"{sid}.json"
        if not path.is_file():
            continue
        stig = json.loads(path.read_text(encoding="utf-8"))
        # Hydrate full rule bodies from rules/by-id for heuristic matching
        full_rules = []
        for summary in stig.get("rules") or []:
            rid = summary.get("full_rule_id")
            if not rid:
                continue
            rpath = data / "rules" / "by-id" / f"{rule_path_id(rid)}.json"
            if rpath.is_file():
                full_rules.append(json.loads(rpath.read_text(encoding="utf-8")))
            else:
                full_rules.append(summary)
        stig["rules"] = full_rules
        stig = enrich_stig(stig, curated)
        if entry.get("quicklink_id") and not stig.get("quicklink_id"):
            stig["quicklink_id"] = entry["quicklink_id"]
        stigs.append(stig)

    log.info("Loaded %s STIG files; maps=%s", len(stigs), sorted(maps.keys()))
    stigs, exports = attach_intune_to_stigs(stigs, catalog=catalog, maps=maps)
    log.info("Product exports: %s", len(exports))

    rules_updated = 0
    for stig in stigs:
        if not stig.get("quicklink_id"):
            continue
        # Write STIG detail with lighter rule summaries (keep titles + intune status)
        detail = dict(stig)
        detail["rules"] = [
            {
                "full_rule_id": r.get("full_rule_id"),
                "title": r.get("title"),
                "severity": r.get("severity"),
                "group_id": r.get("group_id"),
                "intuneStatus": (r.get("intune") or {}).get("status"),
                "hasIntune": (r.get("intune") or {}).get("status") == "mapped",
            }
            for r in (stig.get("rules") or [])
        ]
        # Prefer not to shrink existing detail if it already has richer fields —
        # only update intune-related fields on embedded rules when present.
        existing_path = data / "stigs" / "by-id" / f"{stig['id']}.json"
        if existing_path.is_file():
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            by_rid = {
                r.get("full_rule_id"): r for r in (stig.get("rules") or []) if r.get("full_rule_id")
            }
            for er in existing.get("rules") or []:
                fr = by_rid.get(er.get("full_rule_id"))
                if fr and fr.get("intune"):
                    er["intune"] = fr["intune"]
            existing["quicklink_id"] = stig.get("quicklink_id")
            _write_json(existing_path, existing)
        else:
            _write_json(existing_path, detail)

        for rule in stig.get("rules") or []:
            rid = rule.get("full_rule_id")
            if not rid or "intune" not in rule:
                continue
            rpath = data / "rules" / "by-id" / f"{rule_path_id(rid)}.json"
            if not rpath.is_file():
                continue
            existing = json.loads(rpath.read_text(encoding="utf-8"))
            existing["intune"] = rule["intune"]
            _write_json(rpath, existing)
            rules_updated += 1

    products_dir = data / "intune" / "products"
    products_dir.mkdir(parents=True, exist_ok=True)
    products_out = []
    for pack in exports:
        prod = pack.get("product") or "unknown"
        _write_json(products_dir / f"{prod}.json", pack)
        counts = pack.get("counts") or {}
        products_out.append(
            {
                "product": prod,
                "stigId": (pack.get("stig") or {}).get("id"),
                "stigName": (pack.get("stig") or {}).get("name"),
                "settings": counts.get("settings"),
                "mappedRules": counts.get("mappedRules"),
                "rules": counts.get("rules"),
                "path": f"intune/products/{prod}.json",
            }
        )

    _write_json(
        data / "intune" / "index.json",
        {"products": products_out, "total": len(products_out)},
    )

    docs_path = data / "search" / "documents.json"
    if docs_path.is_file():
        blob = json.loads(docs_path.read_text(encoding="utf-8"))
        docs = blob.get("documents") or []
        intune_rules = set()
        for stig in stigs:
            for rule in stig.get("rules") or []:
                if (rule.get("intune") or {}).get("status") == "mapped":
                    intune_rules.add(rule.get("full_rule_id"))
        for d in docs:
            if d.get("type") == "rule" and d.get("full_rule_id") in intune_rules:
                d["hasIntune"] = True
        _write_json(docs_path, blob)
        log.info("Search docs with hasIntune mapped: %s", len(intune_rules))

    log.info(
        "Rules updated=%s products=%s",
        rules_updated,
        [(p["product"], p["mappedRules"], p["settings"]) for p in products_out],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
