import zipfile
from pathlib import Path

from stigref_build.package_enrich import (
    attach_package_enrichment,
    parse_ckl_bytes,
    _definition_to_oma_hint,
)


def test_definition_to_oma_hint():
    h = _definition_to_oma_hint(
        "device_vendor_msft_policy_config_devicelock_mindevicepasswordlength"
    )
    assert h is not None
    assert "DeviceLock" in h or "Devicelock" in h or "Policy/Config" in h
    assert "MinDevicePasswordLength" in h or "mindevicepasswordlength" in h.lower()


def test_ckl_parse_if_package_present():
    raw = Path(__file__).resolve().parents[2] / "raw"
    gpo = raw / "U_STIG_GPO_Package_April_2026.zip"
    if not gpo.is_file():
        return
    with zipfile.ZipFile(gpo) as z:
        ckls = [n for n in z.namelist() if n.endswith(".ckl") and "Windows 11" in n]
        assert ckls
        rows = parse_ckl_bytes(z.read(ckls[0]), ckls[0])
        assert len(rows) > 50
        # at least some have GPO refs
        with_gpo = [r for r in rows if r.get("gpoRefs")]
        assert len(with_gpo) > 10


def test_attach_enrichment_smoke():
    raw = Path(__file__).resolve().parents[2] / "raw"
    rules = {
        "SV-253284r958928_rule": {
            "full_rule_id": "SV-253284r958928_rule",
            "group_id": "V-253284",
            "title": "SEHOP",
            "stigs": [
                {
                    "name": "Microsoft Windows 11 Security Technical Implementation Guide",
                    "id": "x",
                }
            ],
        }
    }
    idx = attach_package_enrichment(rules, raw)
    assert "stats" in idx
    if (raw / "U_STIG_GPO_Package_April_2026.zip").is_file():
        pe = rules["SV-253284r958928_rule"].get("packageEnrichment") or {}
        # CKL may map this rule
        assert pe.get("ckl") is not None or idx["stats"].get("cklRuleKeys", 0) > 0
