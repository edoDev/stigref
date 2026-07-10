#!/usr/bin/env python3
"""Rebuild sharded+gzip search index from existing docs (B-041)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stigref_build.search_index import (  # noqa: E402
    load_all_documents,
    write_search_index,
)

log = logging.getLogger("reindex_search")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(__file__).resolve().parents[1]
    search_dir = root / "data" / "search"
    docs = load_all_documents(search_dir)
    if not docs:
        log.error("No documents found under %s", search_dir)
        return 1
    # Drop legacy monolith to shrink repo after sharding
    leg = search_dir / "documents.json"
    leg_gz = search_dir / "documents.json.gz"
    write_search_index(search_dir, docs, write_legacy_monolith=False)
    if leg.is_file():
        leg.unlink()
        log.info("Removed legacy %s", leg)
    if leg_gz.is_file():
        leg_gz.unlink()
        log.info("Removed legacy %s", leg_gz)
    log.info("Reindexed %s documents", len(docs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
