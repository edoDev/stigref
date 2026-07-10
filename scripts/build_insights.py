#!/usr/bin/env python3
"""Rebuild data/stats/insights.json from an existing data/ tree (B-090).

Does not reparse DISA ZIPs — scans rule JSON + indexes already on disk.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stigref_build.insights import build_insights_from_disk, write_insights  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Library Observatory insights JSON")
    ap.add_argument(
        "--data",
        type=Path,
        default=ROOT / "data",
        help="Path to data/ directory (default: repo data/)",
    )
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    data = args.data.resolve()
    if not data.is_dir():
        logging.error("Data dir not found: %s", data)
        return 1
    doc = build_insights_from_disk(data)
    path = write_insights(data, doc)
    k = doc.get("kpis") or {}
    print(
        f"OK {path} — stigs={k.get('stigs')} rules={k.get('rules')} "
        f"intuneProducts={k.get('intuneProducts')} uniqueCcis={k.get('uniqueCcis')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
