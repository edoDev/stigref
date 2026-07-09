"""Suggest Intune CSP settings for STIG rules (curated + heuristic)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from stigref_build.tags import load_curated

log = logging.getLogger(__name__)

PKG = Path(__file__).resolve().parent
CSP_SEED = PKG / "csp" / "catalog_seed.json"
MAPS_DIR = PKG / "intune_maps"

REG_PATH_RE = re.compile(
    r"(?:HKEY_LOCAL_MACHINE|HKLM|HKEY_CURRENT_USER|HKCU)"
    r"[\\/][^\s\"'<>]+",
    re.IGNORECASE,
)
REG_VALUE_RE = re.compile(
    r"Registry\s+Path\s*:\s*(.+)$|"
    r"Registry\s+Hive\s*:\s*(.+)$|"
    r"Registry\s+Name\s*:\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)

POLICY_SEARCH = (
    "https://learn.microsoft.com/en-us/windows/client-management/mdm/"
    "policy-configuration-service-provider"
)


def _parse_map_yaml(text: str) -> dict[str, Any]:
    """Minimal YAML subset for map files (same style as curated_tags)."""
    data: dict[str, Any] = {"rules": []}
    section: str | None = None
    current_rule: dict[str, Any] | None = None
    current_sug: dict[str, Any] | None = None
    in_suggestions = False

    for raw in text.splitlines():
        if "#" in raw:
            # keep quoted hashes unlikely; strip comments
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
        # top-level key: value
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            key, val = m.group(1), m.group(2).strip()
            section = key
            in_suggestions = False
            current_rule = None
            current_sug = None
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
        # - rule_id:
        if re.match(r"^\s*-\s+rule_id:", line) or re.match(r"^\s*-\s+full_rule_id:", line):
            current_rule = {}
            data["rules"].append(current_rule)
            in_suggestions = False
            current_sug = None
            k, v = line.strip()[2:].split(":", 1)
            current_rule[k.strip()] = v.strip().strip("\"'")
            continue
        if current_rule is None:
            continue
        if re.match(r"^\s+suggestions:\s*$", line):
            in_suggestions = True
            current_rule["suggestions"] = []
            current_sug = None
            continue
        if in_suggestions and re.match(r"^\s+-\s+csp_id:", line):
            current_sug = {}
            current_rule.setdefault("suggestions", []).append(current_sug)
            _, v = line.strip()[2:].split(":", 1)
            current_sug["csp_id"] = v.strip().strip("\"'")
            continue
        if current_sug is not None and ":" in line.strip():
            k, v = line.strip().split(":", 1)
            current_sug[k.strip()] = v.strip().strip("\"'")
            continue
        if not in_suggestions and ":" in line.strip() and current_rule is not None:
            k, v = line.strip().split(":", 1)
            if k.strip() != "suggestions":
                current_rule[k.strip()] = v.strip().strip("\"'")
    return data


def load_csp_catalog(path: Path | None = None) -> dict[str, Any]:
    path = path or CSP_SEED
    data = json.loads(path.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in data.get("entries") or []}
    data["_by_id"] = by_id
    return data


def load_all_maps(maps_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    maps_dir = maps_dir or MAPS_DIR
    out: dict[str, dict[str, Any]] = {}
    if not maps_dir.is_dir():
        return out
    for f in sorted(maps_dir.glob("*.yaml")):
        try:
            parsed = _parse_map_yaml(f.read_text(encoding="utf-8"))
            product = parsed.get("product") or f.stem
            out[product] = parsed
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to parse map %s: %s", f, exc)
    return out


def _normalize_reg(path: str) -> str:
    p = path.strip().strip("\"'").upper()
    p = p.replace("HKEY_LOCAL_MACHINE", "HKLM").replace("HKEY_CURRENT_USER", "HKCU")
    p = p.replace("/", "\\")
    while "\\\\" in p:
        p = p.replace("\\\\", "\\")
    return p.rstrip("\\")


def extract_registry_paths(text: str) -> list[str]:
    found: list[str] = []
    for m in REG_PATH_RE.finditer(text or ""):
        found.append(_normalize_reg(m.group(0)))
    # Hive + Path patterns on separate lines
    hive = None
    for line in (text or "").splitlines():
        lm = re.search(r"Registry\s+Hive\s*:\s*(.+)", line, re.I)
        if lm:
            hive = lm.group(1).strip()
            continue
        pm = re.search(r"Registry\s+Path\s*:\s*(.+)", line, re.I)
        if pm and hive:
            found.append(_normalize_reg(hive.rstrip("\\") + "\\" + pm.group(1).strip().lstrip("\\")))
    # de-dupe
    seen = set()
    out = []
    for p in found:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _entry_to_suggestion(
    entry: dict[str, Any],
    *,
    value: str | None,
    confidence: str,
    rationale: str,
    kind: str | None = None,
    source: str,
) -> dict[str, Any]:
    kind = kind or entry.get("kind") or "native"
    oma = entry.get("omaUriDevice") or entry.get("omaUriUser") or ""
    return {
        "cspId": entry.get("id"),
        "title": entry.get("title") or entry.get("name"),
        "area": entry.get("area"),
        "name": entry.get("name"),
        "kind": kind,
        "scope": entry.get("scope") or ["device"],
        "omaUri": oma,
        "dataType": entry.get("dataType") or "string",
        "value": value,
        "confidence": confidence,
        "rationale": rationale,
        "learnUrl": entry.get("learnUrl") or POLICY_SEARCH,
        "description": entry.get("description") or "",
        "source": source,
    }


def curated_suggestions_for_rule(
    full_rule_id: str,
    product_map: dict[str, Any],
    catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = catalog.get("_by_id") or {}
    out: list[dict[str, Any]] = []
    for row in product_map.get("rules") or []:
        rid = row.get("full_rule_id") or row.get("rule_id") or ""
        if not rid:
            continue
        if full_rule_id != rid and not full_rule_id.startswith(rid):
            continue
        for sug in row.get("suggestions") or []:
            csp_id = sug.get("csp_id")
            entry = by_id.get(csp_id, {})
            if not entry and not sug.get("omaUri"):
                log.debug("Unknown csp_id %s for %s", csp_id, full_rule_id)
                entry = {
                    "id": csp_id,
                    "title": csp_id,
                    "name": csp_id,
                    "kind": sug.get("kind") or "native",
                    "learnUrl": POLICY_SEARCH,
                }
            item = _entry_to_suggestion(
                entry,
                value=sug.get("value"),
                confidence=sug.get("confidence") or "high",
                rationale=sug.get("rationale") or "Curated mapping",
                kind=sug.get("kind"),
                source="curated",
            )
            if sug.get("omaUri"):
                item["omaUri"] = sug["omaUri"]
            if sug.get("learnUrl"):
                item["learnUrl"] = sug["learnUrl"]
            if sug.get("title"):
                item["title"] = sug["title"]
            out.append(item)
    return out


def heuristic_suggestions_for_rule(
    rule: dict[str, Any],
    catalog: dict[str, Any],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    text = "\n".join(
        [
            rule.get("title") or "",
            rule.get("check") or "",
            rule.get("fix") or "",
            rule.get("description") or "",
        ]
    )
    regs = extract_registry_paths(text)
    text_l = text.lower()
    hits: list[tuple[int, dict[str, Any]]] = []

    for entry in catalog.get("entries") or []:
        score = 0
        reasons: list[str] = []
        for rp in entry.get("registryPaths") or []:
            nr = _normalize_reg(rp)
            for found in regs:
                if nr in found or found in nr:
                    score += 40
                    reasons.append(f"registry overlap ({found})")
                    break
        for kw in entry.get("keywords") or []:
            if kw.lower() in text_l:
                score += 8
                reasons.append(f"keyword:{kw}")
        name = (entry.get("name") or "").lower()
        title = (entry.get("title") or "").lower()
        if name and name in text_l.replace(" ", ""):
            score += 12
            reasons.append("csp name in text")
        if title and title in text_l:
            score += 10
            reasons.append("csp title in text")
        if score >= 16:
            conf = "high" if score >= 40 else "medium" if score >= 24 else "low"
            value = None
            hints = entry.get("valueHints") or {}
            # crude value guess
            if re.search(r"\bmust be (?:disabled|set to ['\"]?0)", text_l):
                value = hints.get("disabled") or "0"
            elif re.search(r"\bmust be (?:enabled|set to ['\"]?1)", text_l):
                value = hints.get("enabled") or "1"
            sug = _entry_to_suggestion(
                entry,
                value=value,
                confidence=conf,
                rationale="Heuristic: " + "; ".join(reasons[:3]),
                source="heuristic",
            )
            hits.append((score, sug))

    hits.sort(key=lambda x: (-x[0], x[1].get("title") or ""))
    # de-dupe by cspId
    seen = set()
    out = []
    for _, sug in hits:
        cid = sug.get("cspId")
        if cid in seen:
            continue
        seen.add(cid)
        out.append(sug)
        if len(out) >= limit:
            break
    return out


def merge_suggestions(
    curated: list[dict[str, Any]],
    heuristic: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen = set()
    out: list[dict[str, Any]] = []
    for s in curated + heuristic:
        key = s.get("cspId") or s.get("omaUri")
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def empty_intune_payload() -> dict[str, Any]:
    return {
        "suggestions": [],
        "status": "unmapped",
        "policySearchUrl": POLICY_SEARCH,
        "message": "No Intune CSP mapping yet for this rule. Search Policy CSP docs or contribute a map entry.",
    }


def suggest_for_rule(
    rule: dict[str, Any],
    *,
    product: str | None,
    maps: dict[str, dict[str, Any]],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    curated: list[dict[str, Any]] = []
    if product and product in maps:
        curated = curated_suggestions_for_rule(
            rule.get("full_rule_id") or rule.get("id") or "",
            maps[product],
            catalog,
        )
    heuristic = heuristic_suggestions_for_rule(rule, catalog)
    merged = merge_suggestions(curated, heuristic)
    if not merged:
        return empty_intune_payload()
    return {
        "suggestions": merged,
        "status": "mapped",
        "policySearchUrl": POLICY_SEARCH,
        "message": None,
        "multiOption": len(merged) > 1,
    }


def product_export(
    *,
    product: str,
    stig: dict[str, Any],
    rules: list[dict[str, Any]],
    catalog: dict[str, Any],
    maps: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Exportable JSON describing a product-level Intune custom policy draft
    (OMA-URI list) aggregated from rule suggestions.
    """
    settings: list[dict[str, Any]] = []
    by_oma: dict[str, dict[str, Any]] = {}
    rule_links: list[dict[str, Any]] = []

    for rule in rules:
        payload = suggest_for_rule(
            rule, product=product, maps=maps, catalog=catalog
        )
        rule_links.append(
            {
                "full_rule_id": rule.get("full_rule_id"),
                "title": rule.get("title"),
                "status": payload["status"],
                "suggestionCount": len(payload.get("suggestions") or []),
            }
        )
        for sug in payload.get("suggestions") or []:
            oma = sug.get("omaUri") or ""
            if not oma:
                continue
            # first wins for aggregate value; keep alternatives listed
            if oma not in by_oma:
                by_oma[oma] = {
                    "name": sug.get("title") or sug.get("name"),
                    "omaUri": oma,
                    "dataType": sug.get("dataType") or "string",
                    "value": sug.get("value"),
                    "kind": sug.get("kind"),
                    "confidence": sug.get("confidence"),
                    "learnUrl": sug.get("learnUrl"),
                    "cspId": sug.get("cspId"),
                    "sourceRules": [rule.get("full_rule_id")],
                }
            else:
                by_oma[oma].setdefault("sourceRules", []).append(
                    rule.get("full_rule_id")
                )

    settings = list(by_oma.values())
    settings.sort(key=lambda s: (s.get("name") or ""))

    return {
        "format": "stigref-intune-product-export/v1",
        "product": product,
        "stig": {
            "id": stig.get("id"),
            "name": stig.get("name"),
            "version": stig.get("version"),
            "release": stig.get("release"),
            "family": stig.get("family"),
        },
        "generatedFrom": {
            "cspCatalogVersion": catalog.get("version"),
            "mapVersion": (maps.get(product) or {}).get("version"),
        },
        "usage": {
            "intuneCustomProfile": (
                "Create an Intune Windows custom configuration profile and add each "
                "OMA-URI row. Prefer Settings Catalog when a native setting exists. "
                "ADMX-backed values may need SyncML <enabled/> payloads — see Learn links."
            ),
            "policyCspIndex": POLICY_SEARCH,
            "disclaimer": (
                "Suggestions are assistive, not authoritative. Validate against STIG "
                "checks, organizational policy, and current Microsoft documentation. "
                "Mappings may be multi-option or incomplete."
            ),
        },
        "settings": settings,
        "rulesSummary": rule_links,
        "counts": {
            "rules": len(rules),
            "mappedRules": sum(1 for r in rule_links if r["suggestionCount"] > 0),
            "settings": len(settings),
        },
    }


def should_process_stig(stig: dict[str, Any]) -> bool:
    """v1: quick-link products only."""
    return bool(stig.get("quicklink_id"))


def attach_intune_to_stigs(
    stigs: list[dict[str, Any]],
    *,
    catalog: dict[str, Any] | None = None,
    maps: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Mutates rules on stigs in-scope with intune payloads.
    Returns (stigs, product_exports).
    """
    catalog = catalog or load_csp_catalog()
    maps = maps if maps is not None else load_all_maps()
    exports: list[dict[str, Any]] = []

    for stig in stigs:
        if not should_process_stig(stig):
            # still mark rules without payload for UI consistency? skip to save size
            continue
        product = stig.get("quicklink_id")
        rules = stig.get("rules") or []
        for rule in rules:
            rule["intune"] = suggest_for_rule(
                rule, product=product, maps=maps, catalog=catalog
            )
        exports.append(
            product_export(
                product=product,
                stig=stig,
                rules=rules,
                catalog=catalog,
                maps=maps,
            )
        )
    return stigs, exports
