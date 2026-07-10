"""
Index DISA companion packages (GPO + Intune) for STIG enrichment.

Expected (quarterly) under repo raw/:
  U_STIG_GPO_Package_*.zip
  U_Intune_Policy_Package_*.zip

These are extremely useful:
  - GPO: ADMX + GPO backups/checklists for Windows, browsers, Office, Defender, Adobe
  - Intune: importable Settings Catalog / Admin Template / Custom JSON profiles
"""

from __future__ import annotations

import json
import logging
import re
import zipfile
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Map package product labels → match needles against STIG title (any hit = match)
GPO_PRODUCT_MATCHERS: list[tuple[str, list[str]]] = [
    ("Windows 11", ["windows 11"]),
    ("Windows 10", ["windows 10"]),
    ("Windows Server 2025", ["windows server 2025"]),
    ("Windows Server 2022", ["windows server 2022"]),
    ("Windows Server 2019", ["windows server 2019"]),
    ("Windows Server 2016", ["windows server 2016"]),
    ("Windows Server 2012", ["windows server 2012"]),
    ("Microsoft Edge", ["microsoft edge security technical"]),
    ("Google Chrome", ["google chrome"]),
    ("Mozilla Firefox", ["mozilla firefox", "firefox"]),
    ("Internet Explorer 11", ["internet explorer 11", "ie11"]),
    ("Microsoft Defender Antivirus", ["microsoft defender antivirus"]),
    ("Windows Defender Firewall", ["windows defender firewall", "defender firewall with advanced"]),
    ("Office / M365 Apps", ["office 365 proplus", "m365 apps", "microsoft 365 apps", "office 2019"]),
    ("Adobe Acrobat Pro DC", ["adobe acrobat professional", "adobe acrobat pro"]),
    ("Adobe Acrobat Reader DC", ["adobe acrobat reader"]),
]

INTUNE_FILE_MATCHERS: list[tuple[str, list[str]]] = [
    ("Windows 11", ["windows 11"]),
    ("Windows 10", ["windows 10"]),
    ("Microsoft Edge", ["microsoft edge"]),
    ("Google Chrome", ["google chrome", "chrome"]),
    ("Internet Explorer 11", ["internet explorer 11"]),
    ("Microsoft Defender Antivirus", ["microsoft defender antivirus", "defender antivirus"]),
    ("Windows Defender Firewall", ["windows defender firewall", "defender firewall"]),
    ("M365 Apps", ["m365 apps", "office 365", "microsoft 365"]),
    ("Adobe Acrobat Pro DC", ["acrobat pro"]),
    ("Adobe Acrobat Reader DC", ["acrobat reader"]),
    ("OneDrive", ["onedrive"]),
    ("Mozilla Firefox", ["firefox"]),
    (".NET Framework", [".net framework", "net framework"]),
]

# Typical DoD Secure Host Baseline *host* stack (workstation-oriented).
# Not an official exhaustive SHB product list — annotation for discoverability.
SHB_STIG_NEEDLES: list[str] = [
    "windows 11 security technical",
    "windows 10 security technical",
    "microsoft edge security technical",
    "google chrome current windows",
    "microsoft defender antivirus",
    "windows defender firewall with advanced security",
    "office 365 proplus",
    "adobe acrobat reader",
    "internet explorer 11",
]

# Product classes that almost never have DISA GPO/Intune host packages
MANUAL_PLATFORM_NEEDLES: list[tuple[str, str]] = [
    ("network-appliance", r"\b(router|switch|firewall|ndm|wlan|vpn security requirements|idps)\b"),
    ("database", r"\b(sql server|oracle database|mysql|postgresql|mongodb)\b"),
    ("mainframe", r"\b(z/os|racf|acf2|tss)\b"),
    ("appliance-vendor", r"\b(palo alto|juniper|f5 |cisco ios|cisco nx|fortinet)\b"),
    ("container-platform", r"\b(kubernetes|openshift|docker enterprise)\b"),
    ("mobile-mdm", r"\b(android|ios |ipados|mdm service)\b"),
]


def find_package_zips(raw_dir: Path) -> dict[str, Path | None]:
    raw_dir = Path(raw_dir)
    gpo = None
    intune = None
    if raw_dir.is_dir():
        for p in sorted(raw_dir.glob("U_STIG_GPO_Package_*.zip")):
            gpo = p
        for p in sorted(raw_dir.glob("U_Intune_Policy_Package_*.zip")):
            intune = p
        # exact names too
        for name, key in (
            ("U_STIG_GPO_Package_April_2026.zip", "gpo"),
            ("U_Intune_Policy_Package_April_2026.zip", "intune"),
        ):
            cand = raw_dir / name
            if cand.is_file():
                if key == "gpo":
                    gpo = cand
                else:
                    intune = cand
    return {"gpo": gpo, "intune": intune}


def index_gpo_package(zip_path: Path) -> dict[str, Any]:
    products: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as z:
        tops: set[str] = set()
        for n in z.namelist():
            top = n.replace("\\", "/").split("/")[0]
            if top and not re.search(r"\.(txt|docx)$", top, re.I):
                if top not in ("Support Files", "ADMX Templates"):
                    tops.add(top)
        for folder in sorted(tops):
            products.append(
                {
                    "packageLabel": folder,
                    "kind": "gpo",
                    "matchKeys": _keys_from_label(folder),
                }
            )
        readme = ""
        if "ReadMe.txt" in z.namelist():
            readme = z.read("ReadMe.txt").decode("utf-8", errors="replace")[:2000]
    return {
        "filename": zip_path.name,
        "type": "gpo",
        "productCount": len(products),
        "products": products,
        "readmeExcerpt": readme,
        "notes": (
            "DISA STIG GPO Package: ADMX templates, GPO backups, reports, checklists. "
            "Evaluate in a test AD environment before production."
        ),
    }


def index_intune_package(zip_path: Path) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as z:
        for n in z.namelist():
            if n.endswith("/") or not n.lower().endswith(".json"):
                continue
            if "Assignments/" in n.replace("\\", "/"):
                continue
            low = n.lower()
            if "sample" in low:
                continue
            rel = n.replace("\\", "/")
            category = "other"
            if "Settings Catalog/" in rel:
                category = "settings-catalog"
            elif "Administrative Templates/" in rel:
                category = "administrative-templates"
            elif "Device Configurations/" in rel:
                category = "device-configuration"
            elif "Device Management Scripts/" in rel:
                category = "script"
            elif "AppConfiguration" in rel:
                category = "app-configuration"
            base = Path(rel).stem
            profiles.append(
                {
                    "path": rel,
                    "name": base,
                    "category": category,
                    "matchKeys": _keys_from_label(base),
                }
            )
        readme = ""
        if "ReadMe.txt" in z.namelist():
            readme = z.read("ReadMe.txt").decode("utf-8", errors="replace")[:2000]
    return {
        "filename": zip_path.name,
        "type": "intune",
        "profileCount": len(profiles),
        "profiles": profiles,
        "readmeExcerpt": readme,
        "notes": (
            "DISA Intune Policy Package: importable Graph/Intune JSON (Settings Catalog, "
            "Admin Templates, Custom, scripts). Test before production. Checklist mapping "
            "often lives in the companion GPO package."
        ),
    }


def _keys_from_label(label: str) -> list[str]:
    s = label.lower()
    keys = []
    for needle_list in (
        ["windows 11", "windows 10", "server 2025", "server 2022", "server 2019",
         "server 2016", "server 2012", "microsoft edge", "google chrome", "firefox",
         "internet explorer", "defender antivirus", "defender firewall", "m365",
         "office 365", "office 2019", "acrobat pro", "acrobat reader", "onedrive",
         ".net framework"],
    ):
        for n in needle_list:
            if n in s:
                keys.append(n)
    return keys


def _title_matches_keys(title: str, keys: list[str]) -> bool:
    t = title.lower()
    return any(k in t for k in keys)


def match_stig_to_packages(
    stig_name: str,
    gpo_index: dict[str, Any] | None,
    intune_index: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return automation annotations for one STIG title."""
    name = stig_name or ""
    low = name.lower()

    gpo_hits: list[str] = []
    if gpo_index:
        for p in gpo_index.get("products") or []:
            keys = p.get("matchKeys") or []
            # also use curated matchers
            label = p.get("packageLabel") or ""
            if _title_matches_keys(name, keys) or _fuzzy_product_match(name, label):
                gpo_hits.append(label)

    intune_hits: list[dict[str, str]] = []
    if intune_index:
        for p in intune_index.get("profiles") or []:
            keys = p.get("matchKeys") or []
            label = p.get("name") or ""
            if _title_matches_keys(name, keys) or _fuzzy_product_match(name, label):
                intune_hits.append(
                    {
                        "name": label,
                        "category": p.get("category") or "",
                        "path": p.get("path") or "",
                    }
                )

    # curated matcher pass for known products even if zip naming odd
    for label, needles in GPO_PRODUCT_MATCHERS:
        if any(n in low for n in needles) and not gpo_hits:
            # only claim gpo if package indexed something windows-related
            if gpo_index and any(
                any(n in (p.get("packageLabel") or "").lower() for n in needles)
                for p in gpo_index.get("products") or []
            ):
                gpo_hits.append(label)

    has_gpo = bool(gpo_hits)
    has_intune = bool(intune_hits)

    platform_kind = None
    for kind, pattern in MANUAL_PLATFORM_NEEDLES:
        if re.search(pattern, low, re.I):
            platform_kind = kind
            break

    # Manual / no automation package: not in GPO/Intune packages and not a typical host ADMX product
    is_host_admx_class = bool(
        re.search(
            r"windows\s*(10|11|server)|microsoft edge|google chrome|firefox|"
            r"defender antivirus|defender firewall|office 365|m365|acrobat|"
            r"internet explorer|onedrive",
            low,
            re.I,
        )
    )

    tags: list[str] = []
    if has_gpo:
        tags.append("has-gpo-package")
    else:
        tags.append("no-gpo-package")
    if has_intune:
        tags.append("has-intune-package")
    else:
        tags.append("no-intune-package")

    if has_gpo or has_intune:
        tags.append("automation-available")
    else:
        tags.append("no-disa-automation-package")
        if platform_kind or not is_host_admx_class:
            tags.append("manual-or-platform-native")
            if platform_kind:
                tags.append(f"platform:{platform_kind}")

    # SHB-related host stack
    shb = any(n in low for n in SHB_STIG_NEEDLES)
    if shb:
        tags.append("shb-related")

    return {
        "hasGpoPackage": has_gpo,
        "hasIntunePackage": has_intune,
        "gpoProducts": sorted(set(gpo_hits)),
        "intuneProfiles": intune_hits[:20],
        "shbRelated": shb,
        "manualOrPlatformNative": "manual-or-platform-native" in tags,
        "platformKind": platform_kind,
        "tags": tags,
    }


def _fuzzy_product_match(stig_name: str, package_label: str) -> bool:
    s = stig_name.lower()
    p = package_label.lower()
    # extract version-ish tokens
    for token in (
        "windows 11",
        "windows 10",
        "server 2025",
        "server 2022",
        "server 2019",
        "server 2016",
        "microsoft edge",
        "google chrome",
        "defender antivirus",
        "defender firewall",
        "internet explorer",
        "m365",
        "office",
        "acrobat pro",
        "acrobat reader",
        "firefox",
    ):
        if token in s and token in p:
            return True
    return False


def build_package_bundle(raw_dir: Path) -> dict[str, Any]:
    paths = find_package_zips(raw_dir)
    gpo_index = None
    intune_index = None
    if paths["gpo"] and paths["gpo"].is_file():
        try:
            gpo_index = index_gpo_package(paths["gpo"])
            log.info("Indexed GPO package %s (%s products)", paths["gpo"].name, gpo_index["productCount"])
        except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
            # Optional enrichment: fail-soft but escalate visibility (not silent).
            log.error("GPO package index failed — GPO enrichment dropped: %s", exc)
        except Exception as exc:  # noqa: BLE001
            log.exception("GPO package index failed unexpectedly — GPO enrichment dropped")
            log.error("%s", exc)
    else:
        log.info("No GPO package found under %s", raw_dir)

    if paths["intune"] and paths["intune"].is_file():
        try:
            intune_index = index_intune_package(paths["intune"])
            log.info(
                "Indexed Intune package %s (%s profiles)",
                paths["intune"].name,
                intune_index["profileCount"],
            )
        except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
            log.error("Intune package index failed — Intune enrichment dropped: %s", exc)
        except Exception as exc:  # noqa: BLE001
            log.exception(
                "Intune package index failed unexpectedly — Intune enrichment dropped"
            )
            log.error("%s", exc)
    else:
        log.info("No Intune package found under %s", raw_dir)

    return {
        "gpo": gpo_index,
        "intune": intune_index,
        "paths": {
            "gpo": paths["gpo"].name if paths["gpo"] else None,
            "intune": paths["intune"].name if paths["intune"] else None,
        },
    }


def annotate_stig(
    stig: dict[str, Any],
    package_bundle: dict[str, Any],
) -> dict[str, Any]:
    """Merge package automation tags into a STIG dict (mutates tags)."""
    ann = match_stig_to_packages(
        stig.get("name") or "",
        package_bundle.get("gpo"),
        package_bundle.get("intune"),
    )
    tags = set(stig.get("tags") or [])
    for t in ann["tags"]:
        tags.add(t)
    # Real package presence upgrades companion tags
    if ann["hasGpoPackage"]:
        tags.add("gpo-companion")
        tags.discard("no-gpo-package")
    if ann["hasIntunePackage"]:
        tags.add("intune-companion")
        tags.discard("no-intune-package")

    stig["tags"] = sorted(tags)
    stig["automation"] = {
        "hasGpoPackage": ann["hasGpoPackage"],
        "hasIntunePackage": ann["hasIntunePackage"],
        "gpoProducts": ann["gpoProducts"],
        "intuneProfiles": ann["intuneProfiles"],
        "shbRelated": ann["shbRelated"],
        "manualOrPlatformNative": ann["manualOrPlatformNative"],
        "platformKind": ann["platformKind"],
    }
    return stig


def rule_manual_hint(rule: dict[str, Any]) -> dict[str, Any]:
    """
    Obvious rule-level manual check heuristics from check/fix text.
    """
    check = (rule.get("check") or "").lower()
    fix = (rule.get("fix") or "").lower()
    text = check + "\n" + fix
    reasons: list[str] = []
    score = 0

    if "this is a manual check" in text or "manual procedure" in text:
        score += 3
        reasons.append("explicit manual check language")
    if "interview the" in check or "ask the" in check:
        score += 2
        reasons.append("interview-based check")
    if "review documentation" in check or "review the organization" in check:
        score += 2
        reasons.append("documentation review")
    if "no fix available" in fix or "no fix text" in fix:
        score += 1
        reasons.append("limited fix text")

    # policy-amenable signals
    automated_signals = 0
    if re.search(r"hklm\\|hkey_|registry", text):
        automated_signals += 2
    if re.search(r"gpo|group policy|administrative template", text):
        automated_signals += 2
    if re.search(r"powershell|get-itemproperty|secedit", text):
        automated_signals += 1

    if score >= 2 and automated_signals == 0:
        return {
            "checkStyle": "manual",
            "confidence": "high" if score >= 3 else "medium",
            "reasons": reasons,
        }
    if automated_signals >= 2:
        return {
            "checkStyle": "policy-amenable",
            "confidence": "medium",
            "reasons": ["registry/GPO/script signals in check/fix"],
        }
    if score >= 1:
        return {
            "checkStyle": "manual-likely",
            "confidence": "low",
            "reasons": reasons,
        }
    return {
        "checkStyle": "unspecified",
        "confidence": "low",
        "reasons": [],
    }
