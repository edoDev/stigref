"""Parse DISA XCCDF 1.1 STIG/SRG documents into plain dicts."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from defusedxml import ElementTree

from stigref_build.ids import parse_rule_id, stig_id

XCCDF_NS = "http://checklists.nist.gov/xccdf/1.1"
NS = {"x": XCCDF_NS}

# Common CCI identifier @system values seen in the wild
CCI_SYSTEMS = (
    "http://iase.disa.mil/cci",
    "http://cyber.mil/cci",
    "http://public.cyber.mil/stigs/cci",
)
CVE_SYSTEM = "http://cve.mitre.org"

RELEASE_INFO_RE = re.compile(
    r"Release:\s*(?P<release>\d+)\s+Benchmark\s+Date:\s*(?P<date>.+)",
    re.IGNORECASE,
)
METADATA_TAG_RE = re.compile(
    r"(?:&lt;|<)(?P<tag>[A-Za-z0-9_]+)(?:&gt;|>)"
    r"(?P<value>.*?)"
    r"(?:&lt;|<)/(?P=tag)(?:&gt;|>)",
    re.IGNORECASE | re.DOTALL,
)


class ParseError(Exception):
    """Raised when an XCCDF document cannot be parsed into a STIG."""


def get_text(elem: Element | None, default: str = "") -> str:
    if elem is None or elem.text is None:
        return default
    return elem.text.strip()


def _qn(tag: str) -> str:
    return f"{{{XCCDF_NS}}}{tag}"


def _find(elem: Element, tag: str) -> Element | None:
    return elem.find(_qn(tag))


def _findall(elem: Element, tag: str) -> list[Element]:
    return list(elem.findall(_qn(tag)))


def parse_release_date(date_text: str) -> str:
    """Return ISO date (YYYY-MM-DD) from DISA benchmark date strings."""
    text = date_text.strip()
    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    # Last resort: keep raw text so we do not drop the STIG
    return text


def extract_embedded_metadata(description: str) -> dict[str, str]:
    """Pull DISA's HTML/XML-ish tags out of Rule description text."""
    meta: dict[str, str] = {}
    for match in METADATA_TAG_RE.finditer(description or ""):
        tag = match.group("tag")
        value = match.group("value").strip()
        # Keep first occurrence; later tags can be noisy
        meta.setdefault(tag, value)
    return meta


def _ident_values(rule: Element, systems: tuple[str, ...] | str) -> list[str]:
    if isinstance(systems, str):
        systems = (systems,)
    values: list[str] = []
    for ident in _findall(rule, "ident"):
        system = ident.get("system") or ""
        if system in systems:
            text = get_text(ident)
            if text:
                values.append(text)
    return values


def _check_content(rule: Element) -> str:
    # Prefer inline check-content anywhere under the rule
    for check in rule.iter(_qn("check-content")):
        text = get_text(check)
        if text:
            return text
    for ref in rule.iter(_qn("check-content-ref")):
        name = ref.get("name")
        if name:
            return name
    return ""


def _fix_text(rule: Element) -> str:
    fix = _find(rule, "fixtext")
    return get_text(fix) if fix is not None else ""


def _profiles_for_group(benchmark: Element, group_id: str) -> list[str]:
    selected: list[str] = []
    for profile in _findall(benchmark, "Profile"):
        profile_id = profile.get("id") or ""
        for select in _findall(profile, "select"):
            if (
                select.get("idref") == group_id
                and (select.get("selected") or "").lower() == "true"
            ):
                if profile_id:
                    selected.append(profile_id)
                break
    return selected


def parse_xccdf_bytes(data: bytes, source: str = "<memory>") -> dict[str, Any]:
    """Parse XCCDF document bytes into a STIG dict with nested rules."""
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise ParseError(f"Invalid XML in {source}: {exc}") from exc

    # Accept default-ns documents
    if root.tag not in (_qn("Benchmark"), "Benchmark"):
        # Some files may use Benchmark without our expected handling
        local = root.tag.rsplit("}", 1)[-1]
        if local != "Benchmark":
            raise ParseError(f"Root element is not Benchmark in {source}")

    title = get_text(_find(root, "title"))
    if not title:
        raise ParseError(f"Missing Benchmark title in {source}")

    description = get_text(_find(root, "description"))
    version_elem = _find(root, "version")
    if version_elem is None or not get_text(version_elem):
        raise ParseError(f"Missing Benchmark version in {source}")
    version = get_text(version_elem)

    release = "0"
    release_date = ""
    # DISA puts release info in plain-text[@id='release-info'] or first plain-text
    plain_texts = _findall(root, "plain-text")
    release_plain = None
    for pt in plain_texts:
        if (pt.get("id") or "").lower() in ("release-info", "release_info"):
            release_plain = pt
            break
    if release_plain is None and plain_texts:
        release_plain = plain_texts[0]

    if release_plain is not None:
        m = RELEASE_INFO_RE.search(get_text(release_plain))
        if m:
            release = m.group("release")
            release_date = parse_release_date(m.group("date"))
        else:
            # Sometimes only a date or freeform text
            raw = get_text(release_plain)
            if raw:
                release_date = parse_release_date(raw) if re.search(r"\d", raw) else raw

    sid = stig_id(title, version, release)

    rules: list[dict[str, Any]] = []
    for group in _findall(root, "Group"):
        group_id = group.get("id") or ""
        group_title = get_text(_find(group, "title"))
        profiles = _profiles_for_group(root, group_id)

        for rule in _findall(group, "Rule"):
            full_rule_id = (rule.get("id") or "").strip()
            if not full_rule_id:
                continue
            full, rule_base, rule_rev = parse_rule_id(full_rule_id)
            severity = (rule.get("severity") or "").strip().lower()
            rule_title = get_text(_find(rule, "title"))
            rule_description = get_text(_find(rule, "description"))
            metadata = extract_embedded_metadata(rule_description)
            metadata["version"] = get_text(_find(rule, "version"))
            if profiles:
                metadata["mac_profiles"] = profiles

            rules.append(
                {
                    "id": full,
                    "full_rule_id": full,
                    "rule_id": rule_base,
                    "rule_revision": rule_rev,
                    "group_id": group_id,
                    "group_title": group_title,
                    "title": rule_title,
                    "severity": severity,
                    "description": rule_description,
                    "check": _check_content(rule),
                    "fix": _fix_text(rule),
                    "ccis": _ident_values(rule, CCI_SYSTEMS),
                    "cves": _ident_values(rule, CVE_SYSTEM),
                    "metadata": metadata,
                    "stig_ids": [sid],
                }
            )

    return {
        "id": sid,
        "name": title,
        "description": description,
        "version": version,
        "release": release,
        "release_date": release_date,
        "source": source,
        "rule_count": len(rules),
        "rules": rules,
    }


def parse_xccdf_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return parse_xccdf_bytes(path.read_bytes(), source=str(path))
