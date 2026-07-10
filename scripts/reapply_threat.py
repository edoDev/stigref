#!/usr/bin/env python3
"""Re-attach threat (CVE/KEV/ATT&CK keyword) on existing rule JSON files."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stigref_build.threat_enrich import (  # noqa: E402
    attach_threat_to_rules,
    load_kev_ids,
)
from stigref_build.write_data import _write_json  # noqa: E402

log = logging.getLogger("reapply_threat")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(__file__).resolve().parents[1]
    rules_dir = root / "data" / "rules" / "by-id"
    if not rules_dir.is_dir():
        log.error("Missing %s", rules_dir)
        return 1
    kev_cache = root / "raw" / "intel" / "kev.json"
    kev_ids, meta = load_kev_ids(kev_cache, fetch=False)
    log.info("KEV ids=%s fromCache=%s", len(kev_ids), meta.get("fromCache"))

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

    stats = attach_threat_to_rules(rules_by_id, kev_ids)
    with_attack = 0
    for rid, rule in rules_by_id.items():
        if (rule.get("threat") or {}).get("attack"):
            with_attack += 1
        _write_json(paths[rid], rule)

    log.info(
        "Updated %s rules; withCve=%s withKev=%s withAttack=%s",
        stats["rulesTotal"],
        stats["rulesWithCve"],
        stats["rulesWithKev"],
        with_attack,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
