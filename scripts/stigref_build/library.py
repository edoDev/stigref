"""Discover and read XCCDF documents from DISA library / STIG zip layouts."""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path
from typing import Iterator

from stigref_build.parse_xccdf import ParseError, parse_xccdf_bytes

log = logging.getLogger(__name__)


def _is_xccdf_name(name: str) -> bool:
    lower = name.replace("\\", "/").lower()
    if "~$" in lower:
        return False
    return lower.endswith("-xccdf.xml") or lower.endswith("_xccdf.xml")


def _is_nested_stig_zip(name: str) -> bool:
    lower = name.replace("\\", "/").lower()
    base = lower.rsplit("/", 1)[-1]
    return base.endswith(".zip") and (
        "_stig.zip" in base or "_srg.zip" in base or base.endswith("stig.zip")
    )


def iter_xccdf_from_zip(
    zip_path: str | Path,
) -> Iterator[tuple[str, bytes]]:
    """
    Yield (source_label, xml_bytes) for each XCCDF found.

    Supports:
    - A single STIG package zip containing *-xccdf.xml
    - A library zip containing nested *_STIG.zip / *_SRG.zip packages
    """
    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        # Direct XCCDF in this zip
        direct = [n for n in names if _is_xccdf_name(n)]
        nested = [n for n in names if _is_nested_stig_zip(n)]

        for name in direct:
            yield f"{zip_path.name}:{name}", zf.read(name)

        for name in nested:
            try:
                inner_bytes = zf.read(name)
            except (KeyError, RuntimeError, OSError) as exc:
                log.error("Could not read nested zip %s: %s", name, exc)
                continue
            try:
                with zipfile.ZipFile(io.BytesIO(inner_bytes), "r") as inner:
                    for inner_name in inner.namelist():
                        if _is_xccdf_name(inner_name):
                            label = f"{zip_path.name}:{name}:{inner_name}"
                            yield label, inner.read(inner_name)
            except zipfile.BadZipFile as exc:
                log.error("Bad nested zip %s: %s", name, exc)


def iter_xccdf_from_path(path: str | Path) -> Iterator[tuple[str, bytes]]:
    """Accept a .xml file, a STIG zip, or a library zip."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.is_dir():
        for xml in sorted(path.rglob("*.xml")):
            if _is_xccdf_name(xml.name):
                yield str(xml), xml.read_bytes()
        return

    suffix = path.suffix.lower()
    if suffix == ".xml":
        yield str(path), path.read_bytes()
        return

    if suffix == ".zip":
        yield from iter_xccdf_from_zip(path)
        return

    raise ValueError(f"Unsupported input type: {path}")


def parse_all(
    path: str | Path,
) -> tuple[list[dict], list[dict]]:
    """
    Parse all XCCDF docs under path.

    Returns (stigs, errors) where errors are {source, error} dicts.
    """
    stigs: list[dict] = []
    errors: list[dict] = []
    for source, data in iter_xccdf_from_path(path):
        try:
            stigs.append(parse_xccdf_bytes(data, source=source))
        except ParseError as exc:
            log.warning("Skip %s: %s", source, exc)
            errors.append({"source": source, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001 — intentional: record into meta.json
            # Catch-all is deliberate: one bad XCCDF must not abort the library build.
            # Errors are returned to the caller and written into meta.json.
            log.exception("Unexpected error parsing %s", source)
            errors.append({"source": source, "error": str(exc)})
    return stigs, errors
