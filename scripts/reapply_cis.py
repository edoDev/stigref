#!/usr/bin/env python3
"""Apply CIS crosswalk maps to existing data/rules without full library rebuild."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stigref_build.cis_enrich import attach_cis_to_rules, load_all_cis_maps  # noqa: E402
from stigref_build.write_data import _write_json  # noqa: E402

log = logging.getLogger("reapply_cis")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(__file__).resolve().parents[1]
    rules_dir = root / "data" / "rules" / "by-id"
    if not rules_dir.is_dir():
        log.error("Missing %s", rules_dir)
        return 1

    maps = load_all_cis_maps()
    log.info("Loaded %s CIS map file(s)", len(maps))

    rules_by_id: dict[str, dict] = {}
    paths: dict[str, Path] = {}
    for path in rules_dir.glob("*.json"):
        try:
            rule = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.error("Skip %s: %s", path.name, exc)
            continue
        rid = rule.get("full_rule_id") or path.stem
        rules_by_id[rid] = rule
        paths[rid] = path

    stats = attach_cis_to_rules(rules_by_id, maps)
    cis_ids: set[str] = set()
    for rid, rule in rules_by_id.items():
        path = paths[rid]
        if (rule.get("cis") or {}).get("status") == "mapped":
            cis_ids.add(rid)
            _write_json(path, rule)
        else:
            # Drop stale CIS block if present
            if "cis" in rule:
                rule.pop("cis", None)
                _write_json(path, rule)

    from stigref_build.search_patch import patch_search_documents

    def _mut(docs: list) -> None:
        for d in docs:
            if d.get("type") == "rule":
                d["hasCis"] = d.get("full_rule_id") in cis_ids

    n = patch_search_documents(root / "data" / "search", _mut)
    log.info("Patched search hasCis (%s docs)", n)

    index_items = []
    disclaimer = None
    for rid in sorted(cis_ids):
        rule = rules_by_id[rid]
        items = (rule.get("cis") or {}).get("items") or []
        disclaimer = (rule.get("cis") or {}).get("disclaimer") or disclaimer
        index_items.append(
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
        root / "data" / "cis" / "index.json",
        {
            "totalMappedRules": len(cis_ids),
            "mapFiles": stats.get("mapFiles"),
            "disclaimer": disclaimer,
            "rules": index_items,
        },
    )

    log.info(
        "CIS mapped rules=%s / %s (maps=%s)",
        stats["rulesWithCis"],
        stats["rulesTotal"],
        stats["mapFiles"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
