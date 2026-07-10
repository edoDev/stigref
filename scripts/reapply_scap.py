#!/usr/bin/env python3
"""Attach SCAP/OVAL badges to existing rule JSON without full reparse."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stigref_build.scap_enrich import attach_scap_to_rules  # noqa: E402
from stigref_build.write_data import _write_json  # noqa: E402

log = logging.getLogger("reapply_scap")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(__file__).resolve().parents[1]
    rules_dir = root / "data" / "rules" / "by-id"
    rules_by_id: dict[str, dict] = {}
    paths: dict[str, Path] = {}
    for path in rules_dir.glob("*.json"):
        try:
            rule = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rid = rule.get("full_rule_id") or path.stem
        rules_by_id[rid] = rule
        paths[rid] = path

    stats = attach_scap_to_rules(rules_by_id)
    oval_ids: set[str] = set()
    for rid, rule in rules_by_id.items():
        _write_json(paths[rid], rule)
        if (rule.get("scap") or {}).get("hasOval") or (rule.get("scap") or {}).get(
            "hasScapSignal"
        ):
            oval_ids.add(rid)

    from stigref_build.search_patch import patch_search_documents

    def _mut(docs: list) -> None:
        for d in docs:
            if d.get("type") == "rule":
                rid = d.get("full_rule_id")
                r = rules_by_id.get(rid or "")
                scap = (r or {}).get("scap") or {}
                d["hasOval"] = bool(scap.get("hasOval"))
                d["hasScap"] = bool(scap.get("hasScapSignal"))

    n = patch_search_documents(root / "data" / "search", _mut)
    log.info("Patched search SCAP flags (%s docs)", n)

    log.info(
        "SCAP/OVAL: oval=%s scapSignal=%s total=%s",
        stats["rulesWithOval"],
        stats["rulesWithScapSignal"],
        stats["rulesTotal"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
