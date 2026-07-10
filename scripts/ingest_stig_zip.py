#!/usr/bin/env python3
"""
Mid-cycle individual STIG ZIP ingest (B-046).

Merges one or more STIG package ZIPs into an existing data/ tree without a full
library rebuild. Useful for DISA mid-quarter updates.

Usage:
  python ingest_stig_zip.py -i raw/U_Some_STIG.zip
  python ingest_stig_zip.py -i raw/A.zip -i raw/B.zip --out ../data
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stigref_build.ids import rule_path_id  # noqa: E402
from stigref_build.intune_suggest import (  # noqa: E402
    attach_intune_to_stigs,
    load_csp_catalog,
)
from stigref_build.library import parse_all  # noqa: E402
from stigref_build.tags import enrich_stig, load_curated  # noqa: E402
from stigref_build.threat_enrich import attach_threat_to_rules, load_kev_ids  # noqa: E402
from stigref_build.write_data import _write_json, merge_rules_across_stigs  # noqa: E402

log = logging.getLogger("ingest_stig_zip")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingest mid-cycle STIG ZIP(s) into data/")
    p.add_argument("-i", "--input", action="append", required=True, help="STIG zip or xccdf")
    p.add_argument("-o", "--out", type=Path, default=None, help="data/ directory")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    root = Path(__file__).resolve().parents[1]
    out = (args.out or (root / "data")).resolve()
    curated = load_curated()
    catalog = load_csp_catalog()
    kev_cache = root / "raw" / "intel" / "kev.json"
    kev_ids, _ = load_kev_ids(kev_cache, fetch=False)

    all_stigs: list[dict] = []
    errors: list[dict] = []
    for inp in args.input:
        path = Path(inp).resolve()
        if not path.exists():
            log.error("Missing input %s", path)
            return 1
        stigs, errs = parse_all(path)
        errors.extend(errs)
        all_stigs.extend(stigs)
        log.info("Parsed %s STIGs from %s", len(stigs), path.name)

    if not all_stigs:
        log.error("No STIGs parsed")
        return 2

    all_stigs = [enrich_stig(s, curated) for s in all_stigs]
    all_stigs, _exports = attach_intune_to_stigs(all_stigs, catalog=catalog)
    rules_by_id = merge_rules_across_stigs(all_stigs)
    attach_threat_to_rules(rules_by_id, kev_ids)

    # Merge into existing index
    idx_path = out / "stigs" / "index.json"
    existing = {"stigs": [], "total": 0}
    if idx_path.is_file():
        existing = json.loads(idx_path.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in existing.get("stigs") or []}

    for stig in all_stigs:
        sid = stig["id"]
        detail = {
            "id": sid,
            "name": stig.get("name"),
            "description": stig.get("description") or "",
            "version": stig.get("version"),
            "release": stig.get("release"),
            "release_date": stig.get("release_date") or "",
            "rule_count": len(stig.get("rules") or []),
            "family": stig.get("family"),
            "vendor": stig.get("vendor"),
            "roles": stig.get("roles") or [],
            "tags": stig.get("tags") or [],
            "quicklink_id": stig.get("quicklink_id"),
            "rules": [
                {
                    "id": r.get("id"),
                    "full_rule_id": r.get("full_rule_id"),
                    "title": r.get("title"),
                    "severity": r.get("severity"),
                    "group_id": r.get("group_id"),
                }
                for r in (stig.get("rules") or [])
            ],
        }
        _write_json(out / "stigs" / "by-id" / f"{sid}.json", detail)
        by_id[sid] = {
            "id": sid,
            "name": stig.get("name"),
            "version": stig.get("version"),
            "release": stig.get("release"),
            "release_date": stig.get("release_date") or "",
            "rule_count": len(stig.get("rules") or []),
            "family": stig.get("family"),
            "vendor": stig.get("vendor"),
            "roles": stig.get("roles") or [],
            "tags": stig.get("tags") or [],
            "quicklink_id": stig.get("quicklink_id"),
        }

    for rid, rule in rules_by_id.items():
        path_id = rule_path_id(rid)
        _write_json(out / "rules" / "by-id" / f"{path_id}.json", rule)

    stigs_list = sorted(by_id.values(), key=lambda s: s.get("name") or "")
    _write_json(out / "stigs" / "index.json", {"stigs": stigs_list, "total": len(stigs_list)})

    # Patch search documents lightly: reload and upsert
    docs_path = out / "search" / "documents.json"
    if docs_path.is_file():
        blob = json.loads(docs_path.read_text(encoding="utf-8"))
        docs = blob.get("documents") or []
        by_doc = {d.get("id"): d for d in docs}
        for stig in all_stigs:
            by_doc[f"stig:{stig['id']}"] = {
                "id": f"stig:{stig['id']}",
                "type": "stig",
                "title": stig.get("name"),
                "body": (stig.get("description") or "")[:400],
                "route": f"/stigs/{stig['id']}",
                "vendor": stig.get("vendor") or "",
                "version": stig.get("version"),
                "release": stig.get("release"),
            }
        for rid, rule in rules_by_id.items():
            cves = list(rule.get("cves") or [])
            by_doc[f"rule:{rid}"] = {
                "id": f"rule:{rid}",
                "type": "rule",
                "title": rule.get("title") or rid,
                "body": " ".join(
                    [
                        (rule.get("check") or "")[:200],
                        (rule.get("fix") or "")[:200],
                    ]
                ),
                "route": f"/rules/{rule_path_id(rid)}",
                "severity": rule.get("severity") or "",
                "full_rule_id": rid,
                "group_id": rule.get("group_id") or "",
                "ccis": rule.get("ccis") or [],
                "cves": cves,
                "hasIntune": bool((rule.get("intune") or {}).get("suggestions")),
                "hasCve": bool(cves) or bool((rule.get("threat") or {}).get("cves")),
                "inKev": bool((rule.get("threat") or {}).get("inKev")),
                "vendor": "",
            }
        docs = list(by_doc.values())
        _write_json(docs_path, {"documents": docs, "total": len(docs)})

    log.info(
        "Ingest complete: %s STIGs, %s rules (errors=%s) → %s",
        len(all_stigs),
        len(rules_by_id),
        len(errors),
        out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
