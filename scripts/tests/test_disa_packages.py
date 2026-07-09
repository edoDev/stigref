from pathlib import Path

from stigref_build.disa_packages import (
    build_package_bundle,
    match_stig_to_packages,
    rule_manual_hint,
)


def test_package_bundle_indexes_raw_if_present():
    raw = Path(__file__).resolve().parents[2] / "raw"
    bundle = build_package_bundle(raw)
    # May be empty in CI without packages; when present, counts > 0
    if (raw / "U_STIG_GPO_Package_April_2026.zip").is_file():
        assert bundle["gpo"] is not None
        assert bundle["gpo"]["productCount"] >= 10
    if (raw / "U_Intune_Policy_Package_April_2026.zip").is_file():
        assert bundle["intune"] is not None
        assert bundle["intune"]["profileCount"] >= 5


def test_match_windows11_with_synthetic_bundle():
    gpo = {
        "products": [
            {
                "packageLabel": "DoD Windows 11 v2r7",
                "matchKeys": ["windows 11"],
            }
        ]
    }
    intune = {
        "profiles": [
            {
                "name": "DoD Windows 11 STIG v2r7 Settings Catalog",
                "category": "settings-catalog",
                "path": "x.json",
                "matchKeys": ["windows 11"],
            }
        ]
    }
    ann = match_stig_to_packages(
        "Microsoft Windows 11 Security Technical Implementation Guide",
        gpo,
        intune,
    )
    assert ann["hasGpoPackage"]
    assert ann["hasIntunePackage"]
    assert ann["shbRelated"]


def test_match_network_manual():
    ann = match_stig_to_packages(
        "Cisco IOS XE Router NDM Security Technical Implementation Guide",
        None,
        None,
    )
    assert ann["manualOrPlatformNative"]
    assert ann["platformKind"] == "network-appliance"
    assert not ann["hasGpoPackage"]


def test_rule_manual_hint():
    r = rule_manual_hint(
        {
            "check": "This is a manual check. Interview the ISSO and review documentation.",
            "fix": "No fix text available.",
        }
    )
    assert r["checkStyle"] in ("manual", "manual-likely")
