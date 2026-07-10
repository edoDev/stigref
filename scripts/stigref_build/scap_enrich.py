"""SCAP/OVAL presence signals on rules (B-050)."""

from __future__ import annotations

import re
from typing import Any

# Substring match: DISA text often says "OVAL definition" mid-sentence
OVAL_RE = re.compile(r"oval", re.I)
SCAP_RE = re.compile(r"scap", re.I)


def build_scap_payload(rule: dict[str, Any]) -> dict[str, Any]:
    check = rule.get("check") or ""
    fix = rule.get("fix") or ""
    desc = rule.get("description") or ""
    meta = rule.get("checkMeta") or {}
    pe = rule.get("packageEnrichment") or {}
    deviation = pe.get("deviation") or {}
    blob = f"{check}\n{fix}\n{desc}"

    has_oval_text = bool(OVAL_RE.search(blob))
    has_oval_sys = bool(meta.get("hasOvalSystemOrHref") or meta.get("hasOvalInCheckText"))
    has_scap_text = bool(SCAP_RE.search(blob))
    scap_fp = bool(deviation.get("falsePositiveScap"))

    has_oval = has_oval_text or has_oval_sys
    has_scap = has_scap_text or scap_fp or has_oval  # OVAL content implies SCAP family tooling

    return {
        "hasOval": has_oval,
        "hasScapSignal": has_scap,
        "hasOvalInCheckText": has_oval_text,
        "hasOvalSystemOrHref": has_oval_sys,
        "hasScapInText": has_scap_text,
        "scapFalsePositiveNote": scap_fp,
        "checkSystems": meta.get("checkSystems") or [],
        "checkContentRefs": meta.get("checkContentRefs") or [],
        "note": (
            "Public U_ XCCDF often lacks external OVAL files; signals come from check text, "
            "check@system/refs when present, or DISA Intune deviation notes."
        ),
    }


def attach_scap_to_rules(rules_by_id: dict[str, dict]) -> dict[str, int]:
    with_oval = 0
    with_scap = 0
    for rule in rules_by_id.values():
        payload = build_scap_payload(rule)
        rule["scap"] = payload
        if payload.get("hasOval"):
            with_oval += 1
        if payload.get("hasScapSignal"):
            with_scap += 1
    return {
        "rulesWithOval": with_oval,
        "rulesWithScapSignal": with_scap,
        "rulesTotal": len(rules_by_id),
    }
