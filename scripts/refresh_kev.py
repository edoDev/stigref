#!/usr/bin/env python3
"""
Refresh CISA KEV catalog into data/threat/ without a full STIG rebuild.

Preserves linkedRules from the previous data/threat/kev.json when present.
Also updates raw/intel/kev.json cache when raw/ exists.

Usage (from repo root or scripts/):
  python refresh_kev.py
  python refresh_kev.py --no-fetch   # rebuild site JSON from cache only
  python refresh_kev.py --out ../data
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow running as scripts/refresh_kev.py without install
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from stigref_build.threat_enrich import (  # noqa: E402
    load_kev_bundle,
    normalize_cve,
)

log = logging.getLogger("refresh_kev")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _linked_rules_from_existing(kev_path: Path) -> dict[str, list[str]]:
    """Recover CVE → rule id links from the published KEV catalog."""
    out: dict[str, list[str]] = {}
    if not kev_path.is_file():
        return out
    try:
        payload = json.loads(kev_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("Could not read existing KEV for links: %s", exc)
        return out
    for row in payload.get("vulnerabilities") or []:
        if not isinstance(row, dict):
            continue
        cve = normalize_cve(row.get("cveID") or "")
        links = row.get("linkedRules") or []
        if cve and links:
            out[cve] = list(links)
    return out


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh CISA KEV static data")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="data/ directory (default: <repo>/data)",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=None,
        help="KEV raw cache path (default: <repo>/raw/intel/kev.json)",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Do not hit network; use cache only",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    root = _repo_root()
    out_dir = (args.out or (root / "data")).resolve()
    cache_path = (args.cache or (root / "raw" / "intel" / "kev.json")).resolve()

    cve_to_rules = _linked_rules_from_existing(out_dir / "threat" / "kev.json")
    # Prefer previous threat meta stats if present
    prev_stats: dict = {}
    prev_meta_path = out_dir / "threat" / "meta.json"
    if prev_meta_path.is_file():
        try:
            prev = json.loads(prev_meta_path.read_text(encoding="utf-8"))
            prev_stats = prev.get("stats") or {}
        except (OSError, json.JSONDecodeError):
            pass

    kev_ids, kev_meta, kev_entries = load_kev_bundle(
        cache_path,
        fetch=not args.no_fetch,
        cve_to_rules=cve_to_rules,
    )

    if not kev_ids and not kev_entries:
        log.error("No KEV data produced — aborting without write")
        return 1

    linked = sum(1 for e in kev_entries if e.get("linkedRules"))
    _write_json(
        out_dir / "threat" / "kev.json",
        {
            "catalogVersion": kev_meta.get("catalogVersion"),
            "dateReleased": kev_meta.get("dateReleased"),
            "fetchedAt": kev_meta.get("fetchedAt"),
            "source": kev_meta.get("source"),
            "catalogUrl": kev_meta.get("catalogUrl"),
            "count": len(kev_entries),
            "linkedRuleCount": linked,
            "vulnerabilities": kev_entries,
        },
    )
    _write_json(
        out_dir / "threat" / "meta.json",
        {
            "kev": kev_meta,
            "stats": {
                "rulesWithCve": prev_stats.get("rulesWithCve", 0),
                "rulesWithKev": prev_stats.get("rulesWithKev", 0),
                "rulesTotal": prev_stats.get("rulesTotal", 0),
            },
            "disclaimer": (
                "Public CVE/KEV context only. Not a vulnerability scan result."
            ),
        },
    )

    log.info(
        "Wrote KEV catalog: count=%s linked=%s fromCache=%s version=%s",
        len(kev_entries),
        linked,
        kev_meta.get("fromCache"),
        kev_meta.get("catalogVersion"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
