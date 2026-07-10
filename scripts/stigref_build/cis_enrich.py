"""
CIS Benchmark crosswalk enrichment (mapping-only, public-safe).

Does NOT redistribute CIS Benchmark PDF/XML body text. Curated YAML maps
STIG rules → CIS recommendation IDs with relationship + short notes.
Official CIS Benchmark documents remain authoritative.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

PKG = Path(__file__).resolve().parent
MAPS_DIR = PKG / "cis_maps"

DISCLAIMER = (
    "CIS crosswalk is assistive mapping only. Official CIS Benchmark text, "
    "profiles, and assessment procedures are authoritative. Not a substitute "
    "for STIG findings or CIS scoring."
)


def _parse_cis_map_yaml(text: str) -> dict[str, Any]:
    """Minimal YAML subset for cis_maps files."""
    data: dict[str, Any] = {"rules": []}
    section: str | None = None
    current_rule: dict[str, Any] | None = None
    current_cis: dict[str, Any] | None = None
    in_cis = False

    for raw in text.splitlines():
        if "#" in raw:
            in_q = False
            out = []
            for ch in raw:
                if ch in "\"'":
                    in_q = not in_q
                if ch == "#" and not in_q:
                    break
                out.append(ch)
            raw = "".join(out)
        line = raw.rstrip()
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            key, val = m.group(1), m.group(2).strip()
            section = key
            in_cis = False
            current_rule = None
            current_cis = None
            if key == "rules":
                data["rules"] = []
            elif val:
                data[key] = val.strip("\"'")
            continue
        if section == "notes" and line.startswith("  "):
            data["notes"] = (data.get("notes") or "") + line.strip() + "\n"
            continue
        if section != "rules":
            continue
        if re.match(r"^\s*-\s+rule_id:", line) or re.match(
            r"^\s*-\s+full_rule_id:", line
        ):
            current_rule = {}
            data["rules"].append(current_rule)
            in_cis = False
            current_cis = None
            k, v = line.strip()[2:].split(":", 1)
            current_rule[k.strip()] = v.strip().strip("\"'")
            continue
        if current_rule is None:
            continue
        if re.match(r"^\s+cis:\s*$", line):
            in_cis = True
            current_rule["cis"] = []
            current_cis = None
            continue
        if in_cis and re.match(r"^\s+-\s+id:", line):
            current_cis = {}
            current_rule.setdefault("cis", []).append(current_cis)
            _, v = line.strip()[2:].split(":", 1)
            current_cis["id"] = v.strip().strip("\"'")
            continue
        if current_cis is not None and ":" in line.strip():
            k, v = line.strip().split(":", 1)
            current_cis[k.strip()] = v.strip().strip("\"'")
            continue
        if not in_cis and ":" in line.strip():
            k, v = line.strip().split(":", 1)
            if k.strip() != "cis":
                current_rule[k.strip()] = v.strip().strip("\"'")
    return data


def load_all_cis_maps(maps_dir: Path | None = None) -> list[dict[str, Any]]:
    maps_dir = maps_dir or MAPS_DIR
    out: list[dict[str, Any]] = []
    if not maps_dir.is_dir():
        return out
    for f in sorted(maps_dir.glob("*.yaml")):
        if f.name.lower() == "readme.md":
            continue
        try:
            parsed = _parse_cis_map_yaml(f.read_text(encoding="utf-8"))
            parsed["_file"] = f.name
            out.append(parsed)
        except (OSError, UnicodeError, ValueError) as exc:
            log.error("Failed to parse CIS map %s: %s", f, exc)
    return out


def empty_cis_payload() -> dict[str, Any]:
    return {
        "status": "none",
        "items": [],
        "disclaimer": DISCLAIMER,
    }


def cis_items_for_rule(
    full_rule_id: str,
    maps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rid = full_rule_id or ""
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for product_map in maps:
        bench = product_map.get("cisBenchmark") or product_map.get("benchmark") or ""
        bench_ver = product_map.get("cisVersion") or product_map.get("version") or ""
        default_profile = product_map.get("profile") or ""
        product = product_map.get("product") or ""
        for row in product_map.get("rules") or []:
            key = row.get("full_rule_id") or row.get("rule_id") or ""
            if not key:
                continue
            if rid != key and not rid.startswith(key):
                continue
            for c in row.get("cis") or []:
                cid = str(c.get("id") or "").strip()
                if not cid:
                    continue
                dedupe = f"{bench}|{cid}|{c.get('profile') or default_profile}"
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                items.append(
                    {
                        "id": cid,
                        "title": c.get("title") or "",
                        "benchmark": bench,
                        "benchmarkVersion": bench_ver,
                        "profile": c.get("profile") or default_profile,
                        "product": product,
                        "relationship": c.get("relationship") or "related",
                        "confidence": c.get("confidence") or "medium",
                        "notes": c.get("notes") or "",
                        "source": "curated",
                    }
                )
    # Prefer equivalent/high confidence first
    rel_rank = {"equivalent": 0, "related": 1, "partial": 2, "conflict": 3}
    conf_rank = {"high": 0, "medium": 1, "low": 2}
    items.sort(
        key=lambda x: (
            rel_rank.get(str(x.get("relationship")), 9),
            conf_rank.get(str(x.get("confidence")), 9),
            x.get("id") or "",
        )
    )
    return items


def attach_cis_to_rules(
    rules_by_id: dict[str, dict],
    maps: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Mutate rules with cis payloads. Returns stats."""
    maps = maps if maps is not None else load_all_cis_maps()
    mapped = 0
    for rule in rules_by_id.values():
        rid = rule.get("full_rule_id") or rule.get("id") or ""
        items = cis_items_for_rule(rid, maps)
        if items:
            rule["cis"] = {
                "status": "mapped",
                "items": items,
                "disclaimer": DISCLAIMER,
            }
            mapped += 1
        else:
            # omit empty payload to keep rule JSON smaller; UI treats missing as none
            rule.pop("cis", None)
    return {
        "rulesWithCis": mapped,
        "rulesTotal": len(rules_by_id),
        "mapFiles": len(maps),
    }
