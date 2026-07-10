from stigref_build.intune_suggest import (
    extract_registry_paths,
    load_csp_catalog,
    load_all_maps,
    merge_suggestions,
    should_process_stig,
    suggest_for_rule,
)


def test_extract_registry_paths():
    text = r"""
    Registry Hive: HKEY_LOCAL_MACHINE
    Registry Path: \SOFTWARE\Policies\Microsoft\FVE
    Also HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters
    """
    paths = extract_registry_paths(text)
    assert any("FVE" in p for p in paths)
    assert any("LANMANSERVER" in p for p in paths)


def test_curated_windows11_sehop():
    catalog = load_csp_catalog()
    maps = load_all_maps()
    rule = {
        "full_rule_id": "SV-253284r958928_rule",
        "title": "SEHOP must be enabled",
        "check": "",
        "fix": "Enable SEHOP",
    }
    payload = suggest_for_rule(
        rule, product="windows-11", maps=maps, catalog=catalog
    )
    assert payload["status"] == "mapped"
    assert any("SEHOP" in (s.get("title") or "").upper() or "SEHOP" in (s.get("rationale") or "").upper() or "StructuredException" in (s.get("cspId") or "") for s in payload["suggestions"])


def test_merge_ranks_native_high_first():
    merged = merge_suggestions(
        [
            {
                "cspId": "a",
                "kind": "admx-backed",
                "confidence": "low",
                "source": "heuristic",
            }
        ],
        [
            {
                "cspId": "b",
                "kind": "native",
                "confidence": "high",
                "source": "curated",
            }
        ],
    )
    assert merged[0]["cspId"] == "b"


def test_should_process_microsoft_windows():
    assert should_process_stig({"quicklink_id": "edge"})
    assert should_process_stig(
        {
            "name": "Microsoft Windows 10 Security Technical Implementation Guide",
            "vendor": "Microsoft",
            "tags": [],
        }
    )
    assert not should_process_stig(
        {"name": "Some Appliance STIG", "vendor": "Other", "tags": []}
    )


def test_heuristic_smb():
    catalog = load_csp_catalog()
    rule = {
        "full_rule_id": "SV-TEST",
        "title": "SMB v1 protocol must be disabled on the SMB server",
        "check": r"Registry Path includes LanmanServer\Parameters SMB1",
        "fix": r"Set HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters\SMB1 to 0",
    }
    payload = suggest_for_rule(rule, product=None, maps={}, catalog=catalog)
    assert payload["status"] == "mapped"
    assert any(s.get("cspId") == "Policy.LanmanServer.SMB1" for s in payload["suggestions"])


def test_unmapped_empty():
    catalog = load_csp_catalog()
    rule = {
        "full_rule_id": "SV-NONE",
        "title": "Obscure unrelated requirement about purple widgets",
        "check": "widget color",
        "fix": "paint purple",
    }
    payload = suggest_for_rule(rule, product=None, maps={}, catalog=catalog)
    assert payload["status"] == "unmapped"
    assert payload["suggestions"] == []
