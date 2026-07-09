from pathlib import Path

import pytest

from stigref_build.parse_xccdf import ParseError, parse_xccdf_file

TESTDATA = Path(__file__).resolve().parent.parent / "testdata"
FIXTURE = TESTDATA / "sample_stig-xccdf.xml"


def test_parse_sample_fixture():
    stig = parse_xccdf_file(FIXTURE)
    assert stig["name"].startswith("Example Operating System")
    assert stig["version"] == "1"
    assert stig["release"] == "3"
    assert stig["release_date"] == "2026-01-15"
    assert stig["rule_count"] == 2
    assert stig["id"].startswith("example-operating-system")

    rules = {r["full_rule_id"]: r for r in stig["rules"]}
    assert "SV-100001r1_rule" in rules
    assert "SV-100002r2_rule" in rules

    r1 = rules["SV-100001r1_rule"]
    assert r1["severity"] == "high"
    assert r1["rule_id"] == "SV-100001"
    assert r1["rule_revision"] == "1"
    assert r1["group_id"] == "V-100001"
    assert "multi-factor" in r1["check"].lower()
    assert "multi-factor" in r1["fix"].lower()
    assert "CCI-000068" in r1["ccis"]
    assert "CVE-2020-0001" in r1["cves"]
    assert "VulnDiscussion" in r1["metadata"]
    assert "MAC-1_Classified" in r1["metadata"].get("mac_profiles", [])

    r2 = rules["SV-100002r2_rule"]
    assert r2["severity"] == "medium"
    assert r2["rule_revision"] == "2"
    assert "CCI-000044" in r2["ccis"]


def test_parse_missing_title_raises(tmp_path: Path):
    bad = tmp_path / "bad.xml"
    bad.write_text(
        '<?xml version="1.0"?>\n'
        '<Benchmark xmlns="http://checklists.nist.gov/xccdf/1.1">'
        "<version>1</version></Benchmark>",
        encoding="utf-8",
    )
    with pytest.raises(ParseError, match="title"):
        parse_xccdf_file(bad)
