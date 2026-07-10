#!/usr/bin/env python3
"""Rebuild sharded search index (B-041) with plain+gzip shards.

Optionally refreshes rule bodies from data/rules/by-id for better recall
(includes check + fix text, longer budget).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stigref_build.ids import rule_path_id  # noqa: E402
from stigref_build.search_index import (  # noqa: E402
    load_all_documents,
    write_search_index,
)
from stigref_build.write_data import SEARCH_BODY_MAX, _truncate  # noqa: E402

log = logging.getLogger("reindex_search")


def _refresh_bodies_from_rules(docs: list[dict], data_dir: Path) -> int:
    """Rewrite rule document bodies from full rule JSON. Returns updated count."""
    rules_dir = data_dir / "rules" / "by-id"
    if not rules_dir.is_dir():
        log.warning("No rules/by-id under %s — skipping body refresh", data_dir)
        return 0
    updated = 0
    for doc in docs:
        if doc.get("type") != "rule":
            continue
        rid = doc.get("full_rule_id") or str(doc.get("id") or "").removeprefix("rule:")
        if not rid:
            continue
        path = rules_dir / f"{rule_path_id(rid)}.json"
        if not path.is_file():
            # try raw filename match
            alt = rules_dir / f"{rid}.json"
            path = alt if alt.is_file() else path
        if not path.is_file():
            continue
        try:
            rule = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            continue
        cves = rule.get("cves") or []
        body = _truncate(
            " ".join(
                [
                    rule.get("full_rule_id") or rid,
                    rule.get("title") or "",
                    rule.get("check") or "",
                    rule.get("fix") or "",
                    rule.get("group_id") or "",
                    " ".join(rule.get("ccis") or []),
                    " ".join(cves),
                    " ".join((s.get("name") or "") for s in (rule.get("stigs") or [])),
                ]
            ),
            SEARCH_BODY_MAX,
        )
        doc["body"] = body
        doc["title"] = rule.get("title") or doc.get("title") or rid
        doc["full_rule_id"] = rule.get("full_rule_id") or rid
        doc["ccis"] = rule.get("ccis") or doc.get("ccis") or []
        doc["cves"] = cves or doc.get("cves") or []
        doc["stig_names"] = [
            s.get("name") for s in (rule.get("stigs") or []) if s.get("name")
        ] or doc.get("stig_names") or []
        # Enrichment flags if present on rule
        threat = rule.get("threat") or {}
        intune = rule.get("intune") or {}
        cis = rule.get("cis") or {}
        scap = rule.get("scap") or {}
        doc["hasIntune"] = bool(
            intune.get("status") == "mapped" and (intune.get("suggestions") or [])
        )
        doc["hasCve"] = bool(cves) or bool(threat.get("cves"))
        doc["inKev"] = bool(threat.get("inKev"))
        doc["hasAttack"] = bool(threat.get("attack"))
        doc["hasCis"] = bool(cis.get("status") == "mapped" and cis.get("items"))
        doc["hasOval"] = bool(scap.get("hasOval"))
        doc["hasScap"] = bool(scap.get("hasScapSignal") or scap.get("hasOval"))
        updated += 1
    return updated


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild search index shards")
    ap.add_argument(
        "--refresh-bodies",
        action="store_true",
        help="Rebuild rule bodies from data/rules/by-id (check+fix, longer budget)",
    )
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    search_dir = data_dir / "search"
    docs = load_all_documents(search_dir)
    if not docs:
        log.error("No documents found under %s", search_dir)
        return 1

    if args.refresh_bodies:
        n = _refresh_bodies_from_rules(docs, data_dir)
        log.info("Refreshed bodies for %s rule docs (max %s chars)", n, SEARCH_BODY_MAX)

    # Drop legacy monolith if present
    for name in ("documents.json", "documents.json.gz"):
        p = search_dir / name
        if p.is_file():
            p.unlink()
            log.info("Removed legacy %s", p.name)

    write_search_index(
        search_dir,
        docs,
        write_legacy_monolith=False,
        write_plain_shards=True,
    )
    log.info("Reindexed %s documents (plain+gzip shards)", len(docs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
