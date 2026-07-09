from stigref_build.threat_enrich import build_threat_for_rule, normalize_cve


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
