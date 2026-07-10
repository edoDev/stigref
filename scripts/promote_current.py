#!/usr/bin/env python3
"""
Promote a built release tree into the live data/ catalog (B-021).

Typical next-quarter workflow:
  1. Build into a side folder (does not touch live yet):
       python -m stigref_build -i raw/U_SRG-STIG_Library_July_2026.zip \\
         -o ../data/releases/2026-07 --release 2026-07
  2. Optionally archive previous live data (git commit / GH Release asset).
  3. Promote:
       python promote_current.py --from ../data/releases/2026-07

Copies known subtrees into data/ and refreshes root meta.releases list.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

log = logging.getLogger("promote_current")

TREE_DIRS = (
    "stigs",
    "rules",
    "search",
    "controls",
    "ccis",
    "tags",
    "families",
    "intune",
    "csp",
    "threat",
    "packages",
)


def _repo_data() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Promote release tree → live data/")
    p.add_argument(
        "--from",
        dest="src",
        type=Path,
        required=True,
        help="Source release directory (contains meta.json + stigs/…)",
    )
    p.add_argument(
        "--to",
        dest="dst",
        type=Path,
        default=None,
        help="Live data directory (default: <repo>/data)",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    src = args.src.resolve()
    dst = (args.dst or _repo_data()).resolve()
    if not (src / "meta.json").is_file():
        log.error("Source missing meta.json: %s", src)
        return 1
    if src == dst:
        log.error("Source and destination are the same path")
        return 1

    dst.mkdir(parents=True, exist_ok=True)
    for name in TREE_DIRS:
        s = src / name
        d = dst / name
        if d.exists():
            shutil.rmtree(d)
        if s.exists():
            log.info("Copy %s → %s", s, d)
            shutil.copytree(s, d)

    meta = json.loads((src / "meta.json").read_text(encoding="utf-8"))
    # Mark as live storage after promote
    rel = meta.get("release") or {}
    rel["storage"] = "live"
    meta["release"] = rel
    meta["currentRelease"] = rel.get("id") or meta.get("currentRelease")
    # Merge release lists with any prior registry
    reg_path = dst / "releases" / "index.json"
    prior: list = []
    if reg_path.is_file():
        try:
            prior = list(json.loads(reg_path.read_text(encoding="utf-8")).get("releases") or [])
        except (OSError, json.JSONDecodeError):
            prior = []
    merged = [rel]
    for r in prior + list(meta.get("releases") or []):
        if r.get("id") and r.get("id") != rel.get("id"):
            if not any(x.get("id") == r.get("id") for x in merged):
                merged.append(r)
    meta["releases"] = merged
    (dst / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(
        json.dumps(
            {"currentRelease": meta.get("currentRelease"), "releases": merged},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    log.info("Promoted %s → live %s (release %s)", src, dst, meta.get("currentRelease"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
