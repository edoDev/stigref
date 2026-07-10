"""
Deep enrichment from DISA GPO + Intune packages:

- STIG Viewer .ckl checklists (rule → GPO/Intune comment mapping)
- Intune deviations workbook (unsupported / not-native / false positives)
- Settings Catalog JSON (Graph settingDefinitionId inventory)
- ADMX inventory from GPO package
"""

from __future__ import annotations

import io
import json
import logging
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as XET

from defusedxml import ElementTree as ET

from stigref_build.disa_packages import find_package_zips

log = logging.getLogger(__name__)

NS_XLSX = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
}

V_ID_RE = re.compile(r"V-\d+", re.I)
SV_ID_RE = re.compile(r"SV-\d+", re.I)


def _rule_keys(full_rule_id: str, group_id: str = "") -> list[str]:
    keys = set()
    if full_rule_id:
        keys.add(full_rule_id)
        m = re.match(r"(SV-\d+)", full_rule_id, re.I)
        if m:
            keys.add(m.group(1).upper())
    if group_id:
        keys.add(group_id.upper())
        for v in V_ID_RE.findall(group_id):
            keys.add(v.upper())
    for v in V_ID_RE.findall(full_rule_id or ""):
        keys.add(v.upper())
    return [k for k in keys if k]


def parse_ckl_bytes(data: bytes, source_name: str) -> list[dict[str, Any]]:
    """Parse a DISA STIG Viewer .ckl into per-rule automation notes."""
    root = ET.fromstring(data)
    rows: list[dict[str, Any]] = []
    for vuln in root.findall(".//VULN"):
        attrs: dict[str, str] = {}
        for sd in vuln.findall("STIG_DATA"):
            k = (sd.findtext("VULN_ATTRIBUTE") or "").strip()
            val = (sd.findtext("ATTRIBUTE_DATA") or "").strip()
            if k:
                attrs[k] = val
        rule_id = attrs.get("Rule_ID") or ""
        vuln_num = attrs.get("Vuln_Num") or ""
        comments = (vuln.findtext("COMMENTS") or "").strip()
        status = (vuln.findtext("STATUS") or "").strip()
        finding = (vuln.findtext("FINDING_DETAILS") or "").strip()
        if not rule_id and not vuln_num:
            continue

        gpo_refs: list[str] = []
        intune_refs: list[str] = []
        outside_gpo = False
        outside_intune = False
        site_specific = False
        for line in comments.splitlines():
            line = line.strip()
            if not line:
                continue
            low = line.lower()
            if "outside scope" in low or "outside of scope" in low:
                outside_gpo = True
                if "intune" in low:
                    outside_intune = True
            if "site specific" in low:
                site_specific = True
            if line.upper().startswith("GPO") or low.startswith("gpo -") or low.startswith("gpo:"):
                gpo_refs.append(re.sub(r"^[Gg][Pp][Oo]\s*[-:]\s*", "", line).strip())
            if line.upper().startswith("INTUNE") or low.startswith("intune -") or low.startswith("intune:"):
                intune_refs.append(
                    re.sub(r"^[Ii]ntune\s*[-:]\s*", "", line).strip()
                )

        # Combined lines like "GPO - X\nIntune - Y"
        if "gpo -" in comments.lower() and not gpo_refs:
            for m in re.finditer(r"GPO\s*[-:]\s*(.+)", comments, re.I):
                gpo_refs.append(m.group(1).split("\n")[0].strip())
        if "intune -" in comments.lower() and not intune_refs:
            for m in re.finditer(r"Intune\s*[-:]\s*(.+)", comments, re.I):
                intune_refs.append(m.group(1).split("\n")[0].strip())

        rows.append(
            {
                "ruleId": rule_id,
                "vulnNum": vuln_num,
                "title": attrs.get("Rule_Title") or "",
                "severity": attrs.get("Severity") or "",
                "status": status,
                "comments": comments,
                "findingDetails": finding,
                "gpoRefs": [g for g in gpo_refs if g],
                "intuneRefs": [i for i in intune_refs if i],
                "outsideGpoScope": outside_gpo,
                "outsideIntuneScope": outside_intune,
                "siteSpecific": site_specific,
                "sourceCkl": source_name,
            }
        )
    return rows


def index_ckls_from_gpo(zip_path: Path) -> dict[str, dict[str, Any]]:
    """Return map of lookup keys → ckl enrichment row (last wins)."""
    by_key: dict[str, dict[str, Any]] = {}
    if not zip_path or not zip_path.is_file():
        return by_key
    with zipfile.ZipFile(zip_path) as z:
        ckls = [
            n
            for n in z.namelist()
            if n.lower().endswith(".ckl") and "Checklist" in n.replace("\\", "/")
        ]
        log.info("Parsing %s CKL checklists from %s", len(ckls), zip_path.name)
        for name in ckls:
            try:
                rows = parse_ckl_bytes(z.read(name), name)
            except (OSError, RuntimeError, ValueError, KeyError) as exc:
                log.error("CKL parse failed %s: %s", name, exc)
                continue
            except Exception as exc:  # noqa: BLE001
                log.exception("CKL parse failed unexpectedly %s", name)
                log.error("%s", exc)
                continue
            for row in rows:
                for key in _rule_keys(row.get("ruleId") or "", row.get("vulnNum") or ""):
                    by_key[key] = row
    return by_key


def _xlsx_shared_strings(xz: zipfile.ZipFile) -> list[str]:
    ss = XET.fromstring(xz.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in ss.findall("m:si", NS_XLSX):
        texts = [t.text or "" for t in si.findall(".//m:t", NS_XLSX)]
        strings.append("".join(texts))
    return strings


def _xlsx_cell_value(c: XET.Element, strings: list[str]) -> str:
    t = c.get("t")
    v = c.find("m:v", NS_XLSX)
    if v is None or v.text is None:
        return ""
    if t == "s":
        try:
            return strings[int(v.text)]
        except (ValueError, IndexError):
            return ""
    return v.text


def parse_deviations_xlsx(data: bytes) -> list[dict[str, Any]]:
    """Parse Intune deviations workbook into per-V-ID records."""
    rows_out: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(data)) as xz:
        strings = _xlsx_shared_strings(xz)
        wb = XET.fromstring(xz.read("xl/workbook.xml"))
        sheet_names: list[tuple[str, str]] = []
        for i, sh in enumerate(wb.findall("m:sheets/m:sheet", NS_XLSX), start=1):
            sheet_names.append((sh.get("name") or f"sheet{i}", f"xl/worksheets/sheet{i}.xml"))

        for sheet_name, path in sheet_names:
            if path not in xz.namelist():
                continue
            sheet = XET.fromstring(xz.read(path))
            raw_rows: list[list[str]] = []
            for row in sheet.findall("m:sheetData/m:row", NS_XLSX):
                raw_rows.append(
                    [_xlsx_cell_value(c, strings) for c in row.findall("m:c", NS_XLSX)]
                )
            if not raw_rows:
                continue
            # header detection
            header = [h.strip().lower() for h in raw_rows[0]]
            # normalize column indexes
            def col(*names: str) -> int | None:
                for n in names:
                    if n in header:
                        return header.index(n)
                return None

            # some sheets have title row then header
            start = 0
            if "id" not in header and len(raw_rows) > 1:
                header = [h.strip().lower() for h in raw_rows[1]]
                start = 1
            id_i = col("id")
            finding_i = col("finding")
            sev_i = col("severity")
            exp_i = col("explanation")
            csp_i = col("csp registry path", "csp path")
            if id_i is None:
                continue
            category = "deviation"
            low_name = sheet_name.lower()
            if "not native" in low_name:
                category = "not-native-to-intune"
            for raw in raw_rows[start + 1 :]:
                if id_i >= len(raw):
                    continue
                id_cell = raw[id_i].strip()
                if not id_cell or id_cell.lower() == "id":
                    continue
                finding = raw[finding_i].strip() if finding_i is not None and finding_i < len(raw) else ""
                if not finding and not V_ID_RE.search(id_cell):
                    continue
                explanation = (
                    raw[exp_i].strip() if exp_i is not None and exp_i < len(raw) else ""
                )
                csp_path = (
                    raw[csp_i].strip() if csp_i is not None and csp_i < len(raw) else ""
                )
                severity = (
                    raw[sev_i].strip() if sev_i is not None and sev_i < len(raw) else ""
                )
                vuln_ids = [v.upper() for v in V_ID_RE.findall(id_cell)]
                if not vuln_ids:
                    continue
                not_native = (
                    category == "not-native-to-intune"
                    or "not present in intune" in explanation.lower()
                    or "not natively available in intune" in explanation.lower()
                )
                false_positive = "false positive" in explanation.lower()
                for vid in vuln_ids:
                    rows_out.append(
                        {
                            "vulnNum": vid,
                            "finding": finding,
                            "severity": severity,
                            "explanation": explanation,
                            "cspRegistryPath": csp_path,
                            "sheet": sheet_name,
                            "category": category,
                            "notNativeToIntune": not_native,
                            "falsePositiveScap": false_positive,
                        }
                    )
    return rows_out


def index_deviations_from_intune(zip_path: Path) -> dict[str, dict[str, Any]]:
    by_v: dict[str, dict[str, Any]] = {}
    if not zip_path or not zip_path.is_file():
        return by_v
    with zipfile.ZipFile(zip_path) as z:
        xlsx_names = [
            n
            for n in z.namelist()
            if "deviation" in n.lower() and n.lower().endswith(".xlsx")
        ]
        if not xlsx_names:
            return by_v
        name = xlsx_names[0]
        log.info("Parsing deviations workbook %s", name)
        try:
            rows = parse_deviations_xlsx(z.read(name))
        except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
            log.error("Deviations parse failed: %s", exc)
            return by_v
        except Exception as exc:  # noqa: BLE001
            log.exception("Deviations parse failed unexpectedly")
            log.error("%s", exc)
            return by_v
        for row in rows:
            by_v[row["vulnNum"]] = row
        log.info("Indexed %s deviation V-IDs", len(by_v))
    return by_v


def extract_settings_catalog_defs(zip_path: Path) -> list[dict[str, Any]]:
    """Pull settingDefinitionId values from Intune Settings Catalog JSON exports."""
    profiles: list[dict[str, Any]] = []
    if not zip_path or not zip_path.is_file():
        return profiles

    def walk_defs(obj: Any, found: list[str]) -> None:
        if isinstance(obj, dict):
            sid = obj.get("settingDefinitionId")
            if isinstance(sid, str) and sid:
                found.append(sid)
            for v in obj.values():
                walk_defs(v, found)
        elif isinstance(obj, list):
            for i in obj:
                walk_defs(i, found)

    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if "Settings Catalog/" not in name.replace("\\", "/"):
                continue
            if not name.lower().endswith(".json"):
                continue
            if "Assignments/" in name.replace("\\", "/"):
                continue
            try:
                data = json.loads(z.read(name))
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                log.error("Settings Catalog JSON skip %s: %s", name, exc)
                continue
            defs: list[str] = []
            walk_defs(data, defs)
            # unique preserve order
            seen = set()
            uniq = []
            for d in defs:
                if d not in seen:
                    seen.add(d)
                    uniq.append(d)
            # derive OMA-ish hint from definition id
            # device_vendor_msft_policy_config_AREA_NAME → ./Device/Vendor/MSFT/Policy/Config/Area/Name
            oma_hints = []
            for d in uniq[:50]:
                oma_hints.append(_definition_to_oma_hint(d))
            profiles.append(
                {
                    "name": data.get("name") or Path(name).stem,
                    "path": name.replace("\\", "/"),
                    "platforms": data.get("platforms"),
                    "settingCount": data.get("settingCount") or len(uniq),
                    "settingDefinitionIds": uniq,
                    "omaUriHints": [h for h in oma_hints if h],
                }
            )
    log.info("Extracted Settings Catalog defs from %s profiles", len(profiles))
    return profiles


def _definition_to_oma_hint(definition_id: str) -> str | None:
    """
    Best-effort OMA-URI hint from Graph settingDefinitionId.
    Example:
      device_vendor_msft_policy_config_devicelock_mindevicepasswordlength
      → ./Device/Vendor/MSFT/Policy/Config/DeviceLock/MinDevicePasswordLength
    """
    d = definition_id.lower()
    prefix = "device_vendor_msft_policy_config_"
    if not d.startswith(prefix):
        # other families exist; still expose raw id
        return None
    rest = definition_id[len(prefix) :]
    # area_policyname — area is first segment before last policy token(s)
    # Graph uses area_settingname with underscores
    parts = rest.split("_")
    if len(parts) < 2:
        return None
    # Heuristic: first token(s) until known areas is hard; use first as area, rest camel-ish
    area = parts[0]
    name = "".join(p[:1].upper() + p[1:] for p in parts[1:])
    area_cap = area[:1].upper() + area[1:] if area else area
    return f"./Device/Vendor/MSFT/Policy/Config/{area_cap}/{name}"


def index_admx_from_gpo(zip_path: Path) -> list[dict[str, str]]:
    if not zip_path or not zip_path.is_file():
        return []
    out: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path) as z:
        for n in z.namelist():
            if n.lower().endswith(".admx"):
                out.append(
                    {
                        "path": n.replace("\\", "/"),
                        "file": Path(n).name,
                        "vendorHint": n.replace("\\", "/").split("/")[1]
                        if "/" in n.replace("\\", "/")
                        else "",
                    }
                )
    return out


def build_enrichment_indexes(raw_dir: Path) -> dict[str, Any]:
    paths = find_package_zips(raw_dir)
    gpo = paths.get("gpo")
    intune = paths.get("intune")

    ckl_by_key = index_ckls_from_gpo(gpo) if gpo else {}
    deviations_by_v = index_deviations_from_intune(intune) if intune else {}
    settings_catalog = extract_settings_catalog_defs(intune) if intune else []
    admx = index_admx_from_gpo(gpo) if gpo else []

    return {
        "cklByKey": ckl_by_key,
        "deviationsByV": deviations_by_v,
        "settingsCatalogProfiles": settings_catalog,
        "admxFiles": admx,
        "sources": {
            "gpo": gpo.name if gpo else None,
            "intune": intune.name if intune else None,
        },
        "stats": {
            "cklRuleKeys": len(ckl_by_key),
            "deviationVulns": len(deviations_by_v),
            "settingsCatalogProfiles": len(settings_catalog),
            "settingsDefinitionIds": sum(
                len(p.get("settingDefinitionIds") or []) for p in settings_catalog
            ),
            "admxFiles": len(admx),
        },
    }


def enrich_rule_from_packages(
    rule: dict[str, Any],
    indexes: dict[str, Any],
) -> dict[str, Any]:
    """Attach packageEnrichment block onto a rule dict."""
    full = rule.get("full_rule_id") or rule.get("id") or ""
    group = rule.get("group_id") or ""
    keys = _rule_keys(full, group)

    ckl = None
    ckl_map = indexes.get("cklByKey") or {}
    for k in keys:
        if k in ckl_map:
            ckl = ckl_map[k]
            break

    dev = None
    dev_map = indexes.get("deviationsByV") or {}
    for k in keys:
        if k.upper() in dev_map:
            dev = dev_map[k.upper()]
            break
        # V- from SV-253285r… → try V-253285
        m = re.search(r"SV-(\d+)", k, re.I)
        if m:
            vid = f"V-{m.group(1)}"
            if vid in dev_map:
                dev = dev_map[vid]
                break

    # Match settings catalog profiles by product keywords in rule's STIG names
    stig_names = " ".join(
        s.get("name") or "" for s in (rule.get("stigs") or [])
    ).lower()
    title = (rule.get("title") or "").lower()
    sc_hits: list[dict[str, Any]] = []
    for prof in indexes.get("settingsCatalogProfiles") or []:
        pname = (prof.get("name") or "").lower()
        # product-level association only (not per-setting yet)
        tokens = ["windows 11", "windows 10", "edge", "chrome", "defender", "firewall", "m365", "office"]
        if any(t in stig_names and t in pname for t in tokens):
            sc_hits.append(
                {
                    "name": prof.get("name"),
                    "path": prof.get("path"),
                    "settingCount": prof.get("settingCount"),
                }
            )

    package_enrichment = {
        "ckl": None
        if not ckl
        else {
            "sourceCkl": ckl.get("sourceCkl"),
            "status": ckl.get("status"),
            "gpoRefs": ckl.get("gpoRefs") or [],
            "intuneRefs": ckl.get("intuneRefs") or [],
            "outsideGpoScope": ckl.get("outsideGpoScope"),
            "outsideIntuneScope": ckl.get("outsideIntuneScope"),
            "siteSpecific": ckl.get("siteSpecific"),
            "comments": ckl.get("comments"),
        },
        "deviation": None
        if not dev
        else {
            "vulnNum": dev.get("vulnNum"),
            "category": dev.get("category"),
            "notNativeToIntune": dev.get("notNativeToIntune"),
            "falsePositiveScap": dev.get("falsePositiveScap"),
            "explanation": dev.get("explanation"),
            "cspRegistryPath": dev.get("cspRegistryPath"),
            "sheet": dev.get("sheet"),
        },
        "settingsCatalogProfiles": sc_hits[:5],
    }

    # Tags on rule for search/UI
    tags: list[str] = []
    if ckl:
        if ckl.get("outsideGpoScope"):
            tags.append("outside-gpo-scope")
        if ckl.get("gpoRefs"):
            tags.append("ckl-gpo-mapped")
        if ckl.get("intuneRefs"):
            tags.append("ckl-intune-mapped")
        if ckl.get("siteSpecific"):
            tags.append("site-specific")
    if dev:
        if dev.get("notNativeToIntune"):
            tags.append("intune-not-native")
        if dev.get("falsePositiveScap"):
            tags.append("scap-false-positive")

    rule["packageEnrichment"] = package_enrichment
    if tags:
        existing = set(rule.get("enrichmentTags") or [])
        existing.update(tags)
        rule["enrichmentTags"] = sorted(existing)
    return rule


def attach_package_enrichment(
    rules_by_id: dict[str, dict],
    raw_dir: Path,
) -> dict[str, Any]:
    indexes = build_enrichment_indexes(raw_dir)
    mapped_ckl = 0
    mapped_dev = 0
    for rule in rules_by_id.values():
        enrich_rule_from_packages(rule, indexes)
        pe = rule.get("packageEnrichment") or {}
        if pe.get("ckl"):
            mapped_ckl += 1
        if pe.get("deviation"):
            mapped_dev += 1

    public_index = {
        "sources": indexes.get("sources"),
        "stats": {
            **(indexes.get("stats") or {}),
            "rulesWithCklMapping": mapped_ckl,
            "rulesWithDeviation": mapped_dev,
        },
        "settingsCatalogProfiles": [
            {
                "name": p.get("name"),
                "path": p.get("path"),
                "settingCount": p.get("settingCount"),
                "sampleDefinitionIds": (p.get("settingDefinitionIds") or [])[:15],
                "sampleOmaUriHints": (p.get("omaUriHints") or [])[:10],
            }
            for p in (indexes.get("settingsCatalogProfiles") or [])
        ],
        "admxFiles": indexes.get("admxFiles") or [],
        "notes": {
            "ckl": "GPO package Support Files/Checklist Files/*.ckl map rules to GPO/Intune implementation notes.",
            "deviations": "Intune package workbook lists settings not native to Intune, SCAP false positives, CSP registry paths.",
            "settingsCatalog": "Graph settingDefinitionId inventory from DISA Settings Catalog JSON exports.",
            "admx": "ADMX templates shipped in GPO package for Chrome/Edge/Adobe/etc.",
        },
    }
    return public_index
