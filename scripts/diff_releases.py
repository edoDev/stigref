#!/usr/bin/env python3
"""
Compare two release catalog trees at the STIG-index level (B-021 / B-022 foundation).

Works on:
  - live data/  (use path to data/)
  - data/releases/YYYY-MM/

Writes data/diffs/{from}__{to}.json summary (family + stig id added/removed).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

log = logging.getLogger("diff_releases")


def _load_stig_index(root: Path) -> list[dict[str, Any]]:
    path = root / "stigs" / "index.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("stigs") or [])


def _by_family(stigs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for s in stigs:
        fam = s.get("family") or s.get("id") or ""
        # keep highest version/release if duplicates
        prev = out.get(fam)
        if not prev:
            out[fam] = s
            continue
        key = (str(s.get("version") or ""), str(s.get("release") or ""))
        pkey = (str(prev.get("version") or ""), str(prev.get("release") or ""))
        if key >= pkey:
            out[fam] = s
    return out


def diff_indexes(
    from_stigs: list[dict[str, Any]],
    to_stigs: list[dict[str, Any]],
) -> dict[str, Any]:
    a = _by_family(from_stigs)
    b = _by_family(to_stigs)
    families = sorted(set(a) | set(b))
    rows = []
    added_f = removed_f = changed_f = same_f = 0
    for fam in families:
        left = a.get(fam)
        right = b.get(fam)
        if left and not right:
            removed_f += 1
            rows.append(
                {
                    "family": fam,
                    "status": "removed",
                    "before": {
                        "id": left.get("id"),
                        "version": left.get("version"),
                        "release": left.get("release"),
                        "name": left.get("name"),
                    },
                }
            )
        elif right and not left:
            added_f += 1
            rows.append(
                {
                    "family": fam,
                    "status": "added",
                    "after": {
                        "id": right.get("id"),
                        "version": right.get("version"),
                        "release": right.get("release"),
                        "name": right.get("name"),
                    },
                }
            )
        else:
            assert left and right
            if left.get("id") != right.get("id") or (
                left.get("version"),
                left.get("release"),
            ) != (right.get("version"), right.get("release")):
                changed_f += 1
                rows.append(
                    {
                        "family": fam,
                        "status": "changed",
                        "before": {
                            "id": left.get("id"),
                            "version": left.get("version"),
                            "release": left.get("release"),
                        },
                        "after": {
                            "id": right.get("id"),
                            "version": right.get("version"),
                            "release": right.get("release"),
                        },
                        "rules": {
                            "added": [],
                            "removed": [],
                            "changed": [],
                            "note": "Rule-level diff deferred (B-022); compare STIG JSON when needed.",
                        },
                    }
                )
            else:
                same_f += 1
    return {
        "summary": {
            "familiesAdded": added_f,
            "familiesRemoved": removed_f,
            "familiesChanged": changed_f,
            "familiesUnchanged": same_f,
            "fromStigCount": len(from_stigs),
            "toStigCount": len(to_stigs),
        },
        "families": rows,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Diff two stigref release trees")
    p.add_argument("--from", dest="from_dir", type=Path, required=True)
    p.add_argument("--to", dest="to_dir", type=Path, required=True)
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path (default: <to>/../diffs or data/diffs)",
    )
    p.add_argument("--from-id", default=None, help="Label for from release")
    p.add_argument("--to-id", default=None, help="Label for to release")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    from_dir = args.from_dir.resolve()
    to_dir = args.to_dir.resolve()
    try:
        left = _load_stig_index(from_dir)
        right = _load_stig_index(to_dir)
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return 1

    from_id = args.from_id
    to_id = args.to_id
    if not from_id:
        try:
            from_id = json.loads((from_dir / "meta.json").read_text(encoding="utf-8")).get(
                "currentRelease"
            )
        except (OSError, json.JSONDecodeError):
            from_id = from_dir.name
    if not to_id:
        try:
            to_id = json.loads((to_dir / "meta.json").read_text(encoding="utf-8")).get(
                "currentRelease"
            )
        except (OSError, json.JSONDecodeError):
            to_id = to_dir.name

    body = diff_indexes(left, right)
    body["from"] = from_id
    body["to"] = to_id

    if args.out:
        out_path = args.out.resolve()
    else:
        # Prefer data/diffs under repo
        data_root = to_dir if (to_dir / "stigs").is_dir() else to_dir.parent
        if data_root.name == "releases":
            data_root = data_root.parent
        out_path = data_root / "diffs" / f"{from_id}__{to_id}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    log.info(
        "Wrote %s (added=%s removed=%s changed=%s)",
        out_path,
        body["summary"]["familiesAdded"],
        body["summary"]["familiesRemoved"],
        body["summary"]["familiesChanged"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
