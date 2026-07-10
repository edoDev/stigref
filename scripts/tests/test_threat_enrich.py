import json
from pathlib import Path

import pytest

from stigref_build.threat_enrich import (
    build_threat_for_rule,
    load_kev_bundle,
    normalize_cve,
    suggest_attack_for_rule,
    validate_kev_payload,
)


def test_normalize_cve():
    assert normalize_cve("cve-2021-34527") == "CVE-2021-34527"
    assert normalize_cve("CVE-2021-34527") == "CVE-2021-34527"


def test_threat_kev_flag():
    rule = {
        "cves": ["CVE-2021-34527"],
        "title": "Print spooler",
        "check": "",
        "fix": "",
    }
    t = build_threat_for_rule(rule, {"CVE-2021-34527"})
    assert t["status"] == "mapped"
    assert t["inKev"] is True
    assert t["cves"][0]["inKev"] is True
    assert "nvd.nist.gov" in t["cves"][0]["nvdUrl"]


def test_threat_none():
    t = build_threat_for_rule({"cves": [], "title": "x", "check": "", "fix": ""}, set())
    assert t["status"] == "none"


def test_attack_keyword_seed():
    techs = suggest_attack_for_rule(
        {
            "title": "SMBv1 must be disabled",
            "check": "Configure SMB1",
            "fix": "",
            "description": "",
        }
    )
    assert any(t["techniqueId"] == "T1210" for t in techs)


def test_threat_includes_attack_without_cve():
    t = build_threat_for_rule(
        {
            "cves": [],
            "title": "Microsoft Defender Antivirus real-time protection",
            "check": "Microsoft Defender Antivirus must be configured",
            "fix": "",
            "description": "",
        },
        set(),
    )
    assert t["status"] == "suggested"
    assert t["attack"]


def test_attack_not_on_generic_title():
    techs = suggest_attack_for_rule(
        {"title": "The system must do something", "check": "ok", "fix": "", "description": ""}
    )
    assert techs == []


def _minimal_kev(n: int = 120) -> dict:
    vulns = [
        {
            "cveID": f"CVE-2020-{i:05d}",
            "vendorProject": "Test",
            "product": "x",
            "vulnerabilityName": f"Vuln {i}",
            "dateAdded": "2020-01-01",
            "shortDescription": "d",
            "requiredAction": "a",
            "dueDate": "2020-02-01",
            "knownRansomwareCampaignUse": "Unknown",
            "notes": "",
            "cwes": [],
        }
        for i in range(n)
    ]
    return {
        "title": "test",
        "catalogVersion": "test",
        "dateReleased": "2020-01-01",
        "vulnerabilities": vulns,
    }


def test_validate_kev_payload_ok():
    data = validate_kev_payload(_minimal_kev())
    assert len(data["vulnerabilities"]) == 120


def test_validate_kev_payload_rejects_short():
    with pytest.raises(ValueError, match="below minimum"):
        validate_kev_payload(_minimal_kev(5))


def test_validate_kev_payload_rejects_bad_shape():
    with pytest.raises(ValueError):
        validate_kev_payload({"vulnerabilities": "nope"})


def test_load_kev_from_valid_cache(tmp_path: Path):
    cache = tmp_path / "kev.json"
    cache.write_text(json.dumps(_minimal_kev()), encoding="utf-8")
    ids, meta, entries = load_kev_bundle(cache, fetch=False)
    assert len(ids) == 120
    assert meta["fromCache"] is True
    assert len(entries) == 120


def test_load_kev_corrupt_cache_no_raise(tmp_path: Path):
    cache = tmp_path / "kev.json"
    cache.write_text("{not-json", encoding="utf-8")
    ids, meta, entries = load_kev_bundle(cache, fetch=False)
    assert ids == set()
    assert entries == []
    assert meta.get("cacheError") is True
