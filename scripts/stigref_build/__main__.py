"""CLI: python -m stigref_build --input PATH --out DIR"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from stigref_build import __version__
from stigref_build.library import parse_all
from stigref_build.write_data import write_data_tree


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stigref_build",
        description="Build static stigref data/ from DISA XCCDF / library ZIP",
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to XCCDF .xml, STIG .zip, library .zip, or a directory of XML",
    )
    parser.add_argument(
        "--out",
        "-o",
        default=None,
        help="Output data directory (default: <repo>/data)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not remove existing stigs/rules/search trees before write",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Debug logging",
    )
    parser.add_argument(
        "--release",
        default=None,
        help="Release id (e.g. 2026-04). Default: inferred from library filename",
    )
    parser.add_argument(
        "--release-label",
        default=None,
        help="Human label (e.g. 'April 2026'). Default: derived from --release",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"stigref-build {__version__}",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    input_path = Path(args.input).resolve()
    if args.out:
        out_dir = Path(args.out).resolve()
    else:
        # scripts/ is cwd package root's parent when installed editable;
        # default to repo data/ relative to this file
        out_dir = Path(__file__).resolve().parents[2] / "data"

    if not input_path.exists():
        logging.error("Input not found: %s", input_path)
        return 1

    logging.info("Parsing %s …", input_path)
    stigs, errors = parse_all(input_path)
    if not stigs:
        logging.error("No STIGs parsed (%s error(s))", len(errors))
        for err in errors[:10]:
            logging.error("  %s: %s", err["source"], err["error"])
        return 2

    source_file = input_path if input_path.is_file() else None
    # If writing under data/releases/<id>, mark storage path for registry
    storage = "live"
    try:
        parts = out_dir.parts
        if "releases" in parts:
            idx = parts.index("releases")
            if idx + 1 < len(parts):
                storage = f"releases/{parts[idx + 1]}"
    except (ValueError, IndexError):
        storage = "live"

    meta = write_data_tree(
        stigs,
        out_dir,
        source_path=source_file,
        source_filename=input_path.name,
        clean=not args.no_clean,
        errors=errors,
        release_id=args.release,
        release_label=args.release_label,
        storage=storage,
    )
    print(
        f"OK: {meta['counts']['stigs']} stigs, "
        f"{meta['counts']['rules']} rules → {out_dir} "
        f"(release {meta.get('currentRelease')})"
    )
    if errors:
        print(f"Warnings: {len(errors)} parse error(s) (see meta.json)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
