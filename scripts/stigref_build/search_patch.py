"""Helpers for reapply_* scripts to patch search docs then rewrite shards."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from stigref_build.search_index import load_all_documents, write_search_index

log = logging.getLogger(__name__)


def patch_search_documents(
    search_dir: Path,
    mutator: Callable[[list[dict[str, Any]]], None],
) -> int:
    """
    Load all search docs, call mutator(docs) in-place, rewrite shards.
    Returns document count.
    """
    search_dir = Path(search_dir)
    docs = load_all_documents(search_dir)
    if not docs:
        log.warning("No search documents to patch under %s", search_dir)
        return 0
    mutator(docs)
    write_search_index(
        search_dir, docs, write_legacy_monolith=False, write_plain_shards=True
    )
    # remove legacy if present
    for name in ("documents.json", "documents.json.gz"):
        p = search_dir / name
        if p.is_file():
            p.unlink()
    return len(docs)
