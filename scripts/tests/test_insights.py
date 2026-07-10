"""Tests for Library Observatory insights aggregator."""

from __future__ import annotations

import json
from pathlib import Path

from stigref_build.insights import (
    build_insights_from_disk,
    build_insights_from_memory,
    write_insights,
)


def test_build_insights_from_memory_minimal():
    stigs = [
        {
            "id": "stig-a",
            "name": "Windows 11 STIG",
            "vendor": "Microsoft",
            "family": "windows-11",
            "rule_count": 2,
            "roles": ["workstation"],
            "hasGpoPackage": True,
            "hasIntunePackage": True,
            "shbRelated": True,
            "manualOrPlatformNative": False,
        },
        {
            "id": "stig-b",
            "name": "Appliance STIG",
            "vendor": "VendorX",
            "family": "appliance",
            "rule_count": 1,
            "roles": ["network"],
            "hasGpoPackage": False,
            "hasIntunePackage": False,
            "shbRelated": False,
            "manualOrPlatformNative": True,
        },
    ]
    rules = {
        "SV-1_rule": {
            "full_rule_id": "SV-1_rule",
            "title": "Enable encryption",
            "severity": "high",
            "ccis": ["CCI-000001"],
            "stig_ids": ["stig-a"],
            "intune": {
                "suggestions": [
                    {"confidence": "high", "kind": "native", "omaUri": "./x"}
                ]
            },
            "threat": {
                "inKev": False,
                "cves": [],
                "attack": [
                    {
                        "techniqueId": "T1486",
                        "name": "Data Encrypted for Impact",
                    }
                ],
            },
            "cis": {
                "status": "mapped",
                "items": [{"id": "3.1.1", "product": "windows-11"}],
            },
            "scap": {"hasOval": False, "hasScapSignal": True},
            "packageEnrichment": {"ckl": None, "deviation": None},
            "checkAutomation": {"checkStyle": "unspecified"},
        },
        "SV-2_rule": {
            "full_rule_id": "SV-2_rule",
            "title": "Audit log",
            "severity": "medium",
            "ccis": ["CCI-000001", "CCI-000002"],
            "stig_ids": ["stig-a"],
            "intune": {"suggestions": []},
            "threat": {"inKev": False, "cves": [], "attack": []},
            "cis": {"status": "none", "items": []},
            "scap": {"hasOval": False, "hasScapSignal": False},
            "packageEnrichment": {},
            "checkAutomation": {"checkStyle": "manual"},
        },
    }
    doc = build_insights_from_memory(
        stigs,
        rules,
        intune_index={
            "products": [
                {
                    "product": "windows-11",
                    "stigId": "stig-a",
                    "stigName": "Windows 11 STIG",
                    "rules": 2,
                    "mappedRules": 1,
                    "settings": 1,
                }
            ]
        },
        kev_payload={
            "count": 2,
            "catalogVersion": "test",
            "vulnerabilities": [
                {
                    "dateAdded": "2024-01-01",
                    "vendorProject": "Microsoft",
                    "knownRansomwareCampaignUse": "Known",
                },
                {
                    "dateAdded": "2025-06-01",
                    "vendorProject": "Adobe",
                    "knownRansomwareCampaignUse": "Unknown",
                },
            ],
        },
        cis_index={"totalMappedRules": 1, "mapFiles": 1},
        meta={
            "currentRelease": "2026-04",
            "builtAt": "2026-07-10T00:00:00Z",
            "parseErrors": 0,
            "sizes": {"totalMB": 1.0},
            "counts": {"stigs": 2, "rules": 2},
            "releases": [{"id": "2026-04"}],
        },
        search_manifest={"totals": {"bytesGz": 2_500_000}, "shards": [{}, {}]},
    )

    assert doc["format"] == "stigref-insights/v1"
    assert doc["kpis"]["stigs"] == 2
    assert doc["kpis"]["rules"] == 2
    assert doc["severity"]["high"] == 1
    assert doc["severity"]["medium"] == 1
    assert doc["automation"]["stigs"]["both"] == 1
    assert doc["automation"]["stigs"]["neither"] == 1
    assert doc["cci"]["uniqueCcis"] == 2
    assert doc["attack"]["rulesWithAttack"] == 1
    assert doc["kev"]["catalogCount"] == 2
    assert doc["kev"]["ransomwareKnown"] == 1
    assert doc["delta"]["available"] is False
    assert doc["kpis"]["searchTransferMBGz"] == 2.38
    assert len(doc["intuneProducts"]) == 1
    assert doc["intuneProducts"][0]["coveragePct"] == 50.0


def test_write_insights_roundtrip(tmp_path: Path):
    doc = build_insights_from_memory(
        [{"id": "s1", "name": "S", "vendor": "V", "family": "f", "rule_count": 0, "roles": []}],
        {},
        meta={"currentRelease": "x"},
    )
    path = write_insights(tmp_path, doc)
    assert path.is_file()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["kpis"]["stigs"] == 1


def test_build_insights_from_disk_minimal(tmp_path: Path):
    data = tmp_path
    (data / "stigs").mkdir()
    (data / "stigs" / "index.json").write_text(
        json.dumps(
            {
                "stigs": [
                    {
                        "id": "s1",
                        "name": "Test",
                        "vendor": "MS",
                        "family": "win",
                        "rule_count": 1,
                        "roles": ["workstation"],
                        "hasGpoPackage": False,
                        "hasIntunePackage": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    rdir = data / "rules" / "by-id"
    rdir.mkdir(parents=True)
    (rdir / "SV-1.json").write_text(
        json.dumps(
            {
                "full_rule_id": "SV-1_rule",
                "title": "t",
                "severity": "low",
                "ccis": ["CCI-1"],
                "stig_ids": ["s1"],
                "intune": None,
                "threat": {"inKev": False, "cves": [], "attack": []},
                "cis": {"status": "none", "items": []},
                "scap": {},
                "packageEnrichment": {},
                "checkAutomation": {"checkStyle": "unspecified"},
            }
        ),
        encoding="utf-8",
    )
    (data / "meta.json").write_text(
        json.dumps({"currentRelease": "2026-04", "counts": {"stigs": 1, "rules": 1}}),
        encoding="utf-8",
    )
    (data / "intune").mkdir()
    (data / "intune" / "index.json").write_text(
        json.dumps({"products": []}), encoding="utf-8"
    )
    doc = build_insights_from_disk(data)
    assert doc["kpis"]["rules"] == 1
    assert doc["severity"]["low"] == 1
    assert doc["cci"]["uniqueCcis"] == 1
