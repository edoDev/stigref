"""
Optional local CIS extract (B-082) — license-safe path for private builds.

Place operator-maintained JSON under raw/cis/ (gitignored via raw/).
Never commit CIS PDF/XML bodies to a public repository.

Expected file shape (raw/cis/*.json):
{
  "benchmark": "CIS Microsoft Windows 11 Enterprise Benchmark",
  "version": "3.0.0",
  "profile": "Level_1",
  "sourceNote": "Extracted locally from Workbench PDF for private use",
  "recommendations": [
    {
      "id": "18.9.95.1",
      "title": "Ensure SEHOP is enabled",
      "description": "optional longer text from YOUR licensed copy",
      "audit": "optional",
      "remediation": "optional"
    }
  ]
}

These enrich curated cis_maps rows that share the same recommendation id
by filling title/description when the map left them short.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def load_local_cis_extracts(raw_cis_dir: Path) -> dict[str, dict[str, Any]]:
    """
    Return map of recommendation id -> local extract row (last file wins).
    """
    out: dict[str, dict[str, Any]] = {}
    if not raw_cis_dir.is_dir():
        return out
    for path in sorted(raw_cis_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.error("Skip CIS extract %s: %s", path.name, exc)
            continue
        bench = data.get("benchmark") or ""
        ver = data.get("version") or ""
        profile = data.get("profile") or ""
        for rec in data.get("recommendations") or []:
            if not isinstance(rec, dict):
                continue
            rid = str(rec.get("id") or "").strip()
            if not rid:
                continue
            out[rid] = {
                **rec,
                "benchmark": rec.get("benchmark") or bench,
                "benchmarkVersion": rec.get("benchmarkVersion") or ver,
                "profile": rec.get("profile") or profile,
                "_sourceFile": path.name,
            }
        log.info("Loaded local CIS extract %s (%s recs)", path.name, len(data.get("recommendations") or []))
    return out


def enrich_cis_items_with_local(
    items: list[dict[str, Any]],
    local: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge local extract text into curated CIS items by recommendation id."""
    if not local:
        return items
    out = []
    for item in items:
        cid = str(item.get("id") or "")
        loc = local.get(cid)
        if not loc:
            out.append(item)
            continue
        merged = dict(item)
        if not merged.get("title") and loc.get("title"):
            merged["title"] = loc["title"]
        # Optional deep fields only when local extract provides them
        if loc.get("description"):
            merged["localDescription"] = loc["description"]
        if loc.get("audit"):
            merged["localAudit"] = loc["audit"]
        if loc.get("remediation"):
            merged["localRemediation"] = loc["remediation"]
        if loc.get("_sourceFile"):
            merged["localSourceFile"] = loc["_sourceFile"]
        if not merged.get("benchmark") and loc.get("benchmark"):
            merged["benchmark"] = loc["benchmark"]
        merged["hasLocalExtract"] = True
        out.append(merged)
    return out
