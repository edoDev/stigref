from stigref_build.cis_enrich import (
    attach_cis_to_rules,
    cis_items_for_rule,
    load_all_cis_maps,
)


def test_load_maps():
    maps = load_all_cis_maps()
    assert len(maps) >= 1
    assert any(m.get("product") == "windows-11" for m in maps)


def test_sehop_mapping():
    maps = load_all_cis_maps()
    items = cis_items_for_rule("SV-253284r958928_rule", maps)
    assert items
    assert any(i["id"] for i in items)
    assert items[0]["relationship"] in (
        "equivalent",
        "related",
        "partial",
        "conflict",
    )


def test_attach_stats():
    maps = load_all_cis_maps()
    rules = {
        "SV-253284r1_rule": {
            "full_rule_id": "SV-253284r1_rule",
            "title": "SEHOP",
        },
        "SV-NOPE": {"full_rule_id": "SV-NOPE", "title": "x"},
    }
    stats = attach_cis_to_rules(rules, maps)
    assert stats["rulesWithCis"] >= 1
    assert rules["SV-253284r1_rule"]["cis"]["status"] == "mapped"
    assert "cis" not in rules["SV-NOPE"]
