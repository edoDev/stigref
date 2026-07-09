from stigref_build.ids import parse_rule_id, rule_path_id, slugify, stig_id


def test_slugify_basic():
    assert slugify("Red Hat Enterprise Linux 8 STIG") == "red-hat-enterprise-linux-8-stig"


def test_stig_id_stable():
    a = stig_id("Example Operating System Security Technical Implementation Guide", 1, 3)
    b = stig_id("Example Operating System Security Technical Implementation Guide", "1", "3")
    assert a == b
    assert "-v1r3-" in a
    assert a.startswith("example-operating-system-security-technical-implementation-guide-v1r3-")
    assert len(a.rsplit("-", 1)[-1]) == 8


def test_stig_id_changes_with_release():
    a = stig_id("Example OS STIG", 1, 1)
    b = stig_id("Example OS STIG", 1, 2)
    assert a != b


def test_parse_rule_id():
    full, base, rev = parse_rule_id("SV-100001r1_rule")
    assert full == "SV-100001r1_rule"
    assert base == "SV-100001"
    assert rev == "1"


def test_parse_rule_id_fallback():
    full, base, rev = parse_rule_id("CUSTOM-ID")
    assert full == "CUSTOM-ID"
    assert base == "CUSTOM-ID"
    assert rev == ""


def test_rule_path_id_strips_illegal():
    assert ":" not in rule_path_id('SV:100/r1_rule')
