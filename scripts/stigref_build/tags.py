"""Derive vendor / role / curated tags for STIGs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Prefer stdlib for YAML-ish config: we ship curated as simple structure loaded via json-compatible path.
# curated_tags.yaml is small — parse with a minimal loader or json alternative.
# Use pure Python for reliability without PyYAML dep.

FAMILY_STRIP = re.compile(
    r"\s+Security Technical Implementation Guide\s*$|"
    r"\s+Security Requirements Guide\s*$",
    re.I,
)

VENDOR_PREFIXES: list[tuple[str, str]] = [
    # longer first
    ("Red Hat", "Red Hat"),
    ("Palo Alto", "Palo Alto"),
    ("Riverbed", "Riverbed"),
    ("BlackBerry", "BlackBerry"),
    ("Microsoft", "Microsoft"),
    ("VMware", "VMware"),
    ("Cisco", "Cisco"),
    ("Google", "Google"),
    ("Oracle", "Oracle"),
    ("Adobe", "Adobe"),
    ("Apple", "Apple"),
    ("Juniper", "Juniper"),
    ("Symantec", "Symantec"),
    ("Samsung", "Samsung"),
    ("Ivanti", "Ivanti"),
    ("Apache", "Apache"),
    ("IBM", "IBM"),
    ("HPE", "HPE"),
    ("F5", "F5"),
    ("Dell", "Dell"),
    ("Zebra", "Zebra"),
    ("Tanium", "Tanium"),
    ("Trellix", "Trellix"),
    ("Trend Micro", "Trend Micro"),
    ("Canonical", "Canonical"),
    ("SUSE", "SUSE"),
    ("Ubuntu", "Canonical"),
    ("Mozilla", "Mozilla"),
    ("Amazon", "Amazon"),
    ("AWS", "Amazon"),
    ("Kubernetes", "Kubernetes"),
    ("Docker", "Docker"),
    ("Rancher", "Rancher"),
    ("Nutanix", "Nutanix"),
    ("Okta", "Okta"),
    ("Ping", "Ping Identity"),
]

ROLE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("server", re.compile(r"\bserver\b|\brhel\b|\bsles\b|\bulinux\b", re.I)),
    ("workstation", re.compile(r"windows\s*1[01]\b|workstation|desktop|\bmacos\b", re.I)),
    ("browser", re.compile(r"\bchrome\b|\bedge\b|\bfirefox\b|\bbrowser\b", re.I)),
    ("mobile", re.compile(r"\bandroid\b|\bios\b|\bipados\b|\bmdm\b|\bemm\b|\bintune\b", re.I)),
    ("database", re.compile(r"\bsql\b|\boracle\b|\bpostgres|\bmysql\b|\bmongodb\b|\bdatabase\b", re.I)),
    ("network", re.compile(r"\brouter\b|\bswitch\b|\bfirewall\b|\bndm\b|\bidps\b|\bvpn\b|\bwlan\b|\bnetwork\b", re.I)),
    ("cloud", re.compile(r"\bcloud\b|\bkubernetes\b|\bopenshift\b|\bazure\b|\baws\b", re.I)),
    ("application", re.compile(r"\bapplication\b|\bweb server\b|\bapache\b|\biis\b", re.I)),
]


def family_key(name: str) -> str:
    """Stable family key across version/release bumps (title-based)."""
    base = FAMILY_STRIP.sub("", name).strip()
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    return slug or "unknown"


def detect_vendor(name: str) -> str:
    for prefix, vendor in VENDOR_PREFIXES:
        if name.lower().startswith(prefix.lower()) or f" {prefix.lower()}" in f" {name.lower()}":
            # prefer startswith
            if name.lower().startswith(prefix.lower()):
                return vendor
    for prefix, vendor in VENDOR_PREFIXES:
        if name.lower().startswith(prefix.lower()):
            return vendor
    # first token fallback
    token = name.split()[0] if name.split() else "Other"
    if token in ("The", "A", "An"):
        return "Other"
    return token


def detect_roles(name: str) -> list[str]:
    roles: list[str] = []
    for role, pattern in ROLE_RULES:
        if pattern.search(name):
            roles.append(role)
    if not roles:
        roles.append("other")
    return roles


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """
    Minimal YAML subset reader for curated_tags.yaml (no external dep).
    Supports: top keys, lists of maps with scalar values, lists of scalars.
    """
    # Prefer json if file is json; else very small hand parse for our file shape.
    try:
        import json

        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Convert our constrained YAML to something we can eval carefully via line parse
    data: dict[str, Any] = {"quick_links": [], "title_tags": []}
    section: str | None = None
    current: dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^[a-zA-Z0-9_]+:\s*$", line):
            section = line.split(":")[0].strip()
            current = None
            if section not in data:
                data[section] = []
            continue
        if section and line.strip().startswith("- "):
            rest = line.strip()[2:]
            if ":" in rest:
                current = {}
                data[section].append(current)
                k, v = rest.split(":", 1)
                current[k.strip()] = _scalar(v.strip())
            else:
                data[section].append(_scalar(rest))
                current = None
            continue
        if current is not None and ":" in line:
            k, v = line.strip().split(":", 1)
            val = _scalar(v.strip())
            # tags: [a, b]
            if k.strip() == "tags" and isinstance(val, str) and val.startswith("["):
                inner = val.strip()[1:-1]
                current[k.strip()] = [x.strip() for x in inner.split(",") if x.strip()]
            else:
                current[k.strip()] = val
    return data


def _scalar(v: str) -> Any:
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1]
        return [x.strip().strip("\"'") for x in inner.split(",") if x.strip()]
    return v


def load_curated(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).with_name("curated_tags.yaml")
    if not path.is_file():
        return {"quick_links": [], "title_tags": []}
    return _parse_simple_yaml(path.read_text(encoding="utf-8"))


def enrich_stig(stig: dict[str, Any], curated: dict[str, Any] | None = None) -> dict[str, Any]:
    curated = curated or load_curated()
    name = stig.get("name") or ""
    tags: set[str] = set()
    vendor = detect_vendor(name)
    roles = detect_roles(name)
    tags.add(f"vendor:{vendor}")
    for r in roles:
        tags.add(f"role:{r}")

    for rule in curated.get("title_tags") or []:
        match = (rule.get("match") or "").lower()
        if match and match in name.lower():
            for t in rule.get("tags") or []:
                tags.add(str(t))

    quicklink_id = None
    for ql in curated.get("quick_links") or []:
        match = (ql.get("match") or "").lower()
        if match and match in name.lower():
            quicklink_id = ql.get("id")
            tags.add("quicklink")
            tags.add(f"quicklink:{quicklink_id}")
            break

    out = dict(stig)
    out["family"] = family_key(name)
    out["vendor"] = vendor
    out["roles"] = roles
    out["tags"] = sorted(tags)
    if quicklink_id:
        out["quicklink_id"] = quicklink_id
    return out


def build_quick_links(
    stigs: list[dict[str, Any]], curated: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    curated = curated or load_curated()
    by_ql: dict[str, dict[str, Any]] = {}
    for s in stigs:
        qid = s.get("quicklink_id")
        if qid:
            by_ql[qid] = s
    links: list[dict[str, Any]] = []
    for ql in curated.get("quick_links") or []:
        qid = ql.get("id")
        hit = by_ql.get(qid)
        links.append(
            {
                "id": qid,
                "label": ql.get("label") or qid,
                "stigId": hit["id"] if hit else None,
                "stigName": hit["name"] if hit else None,
                "found": hit is not None,
            }
        )
    return links
