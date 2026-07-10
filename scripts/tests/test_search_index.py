import gzip
import json
from pathlib import Path

from stigref_build.search_index import load_all_documents, write_search_index


def test_write_and_load_shards(tmp_path: Path):
    docs = [
        {"id": "stig:a", "type": "stig", "title": "A", "body": "", "route": "/a"},
        {
            "id": "rule:SV-1",
            "type": "rule",
            "title": "R1",
            "body": "x",
            "route": "/r1",
            "full_rule_id": "SV-1",
        },
        {
            "id": "rule:SV-2",
            "type": "rule",
            "title": "R2",
            "body": "y",
            "route": "/r2",
            "full_rule_id": "SV-2",
        },
    ]
    search = tmp_path / "search"
    man = write_search_index(
        search, docs, write_legacy_monolith=False, write_plain_shards=False, rule_shards=4
    )
    assert man["total"] == 3
    assert (search / "manifest.json").is_file()
    assert not (search / "documents.json").exists()

    # gzip shards exist (plain optional / off by default)
    for s in man["shards"]:
        gz = search / s["pathGz"]
        assert gz.is_file()
        with gzip.open(gz, "rt", encoding="utf-8") as f:
            blob = json.loads(f.read())
        assert "documents" in blob

    loaded = load_all_documents(search)
    assert len(loaded) == 3
    types = {d["type"] for d in loaded}
    assert types == {"stig", "rule"}
