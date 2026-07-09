from stigref_build.tags import build_quick_links, detect_roles, detect_vendor, enrich_stig, family_key


def test_vendor_microsoft():
    assert detect_vendor("Microsoft Windows 11 Security Technical Implementation Guide") == "Microsoft"


def test_roles_server_workstation():
    assert "server" in detect_roles("Microsoft Windows Server 2022 Security Technical Implementation Guide")
    assert "workstation" in detect_roles("Microsoft Windows 11 Security Technical Implementation Guide")
    assert "browser" in detect_roles("Microsoft Edge Security Technical Implementation Guide")


def test_family_stable():
    a = family_key("Microsoft Windows 11 Security Technical Implementation Guide")
    b = family_key("Microsoft Windows 11 Security Technical Implementation Guide")
    assert a == b
    assert "windows-11" in a


def test_enrich_quicklink():
    stig = {
        "id": "x",
        "name": "Microsoft Windows 11 Security Technical Implementation Guide",
        "version": "2",
        "release": "7",
        "rules": [],
    }
    out = enrich_stig(stig)
    assert out["vendor"] == "Microsoft"
    assert out.get("quicklink_id") == "windows-11"
    assert "intune-companion" in out["tags"]


def test_build_quick_links():
    stigs = [
        enrich_stig(
            {
                "id": "win11-id",
                "name": "Microsoft Windows 11 Security Technical Implementation Guide",
                "version": "2",
                "release": "7",
                "rules": [],
            }
        )
    ]
    links = build_quick_links(stigs)
    win = next(x for x in links if x["id"] == "windows-11")
    assert win["found"] is True
    assert win["stigId"] == "win11-id"
