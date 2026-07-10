from stigref_build.scap_enrich import attach_scap_to_rules, build_scap_payload


def test_oval_in_check_text():
    p = build_scap_payload(
        {
            "check": "Evaluate the OVAL definition for this setting",
            "fix": "",
            "checkMeta": {},
            "packageEnrichment": {},
        }
    )
    assert p["hasOval"] is True
    assert p["hasScapSignal"] is True


def test_scap_false_positive_note():
    p = build_scap_payload(
        {
            "check": "registry check",
            "fix": "",
            "checkMeta": {},
            "packageEnrichment": {
                "deviation": {"falsePositiveScap": True, "explanation": "FP"}
            },
        }
    )
    assert p["scapFalsePositiveNote"] is True
    assert p["hasScapSignal"] is True


def test_attach_counts():
    rules = {
        "a": {
            "full_rule_id": "a",
            "check": "oval definition xyz",
            "fix": "",
            "packageEnrichment": {},
        },
        "b": {
            "full_rule_id": "b",
            "check": "plain text",
            "fix": "",
            "packageEnrichment": {},
        },
    }
    stats = attach_scap_to_rules(rules)
    assert stats["rulesWithOval"] == 1
    assert rules["a"]["scap"]["hasOval"] is True
