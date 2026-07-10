import json
import zipfile
from pathlib import Path

from stigref_build.library import parse_all
from stigref_build.write_data import write_data_tree

TESTDATA = Path(__file__).resolve().parent.parent / "testdata"
FIXTURE = TESTDATA / "sample_stig-xccdf.xml"


def test_write_data_tree_from_xml(tmp_path: Path):
    stigs, errors = parse_all(FIXTURE)
    assert not errors
    assert len(stigs) == 1

    meta = write_data_tree(
        stigs,
        tmp_path / "data",
        source_path=FIXTURE,
        source_filename=FIXTURE.name,
    )
    assert meta["counts"]["stigs"] == 1
    assert meta["counts"]["rules"] == 2
    assert meta["counts"]["searchDocuments"] == 3  # 1 stig + 2 rules
    assert meta["source"]["filename"] == "sample_stig-xccdf.xml"
    assert meta["source"]["sha256"]

    data = tmp_path / "data"
    meta_disk = json.loads((data / "meta.json").read_text(encoding="utf-8"))
    assert meta_disk["counts"]["rules"] == 2

    index = json.loads((data / "stigs" / "index.json").read_text(encoding="utf-8"))
    assert index["total"] == 1
    stig_id = index["stigs"][0]["id"]

    detail = json.loads(
        (data / "stigs" / "by-id" / f"{stig_id}.json").read_text(encoding="utf-8")
    )
    assert detail["rule_count"] == 2
    assert len(detail["rules"]) == 2

    rule_path = data / "rules" / "by-id" / "SV-100001r1_rule.json"
    assert rule_path.is_file()
    rule = json.loads(rule_path.read_text(encoding="utf-8"))
    assert rule["severity"] == "high"
    assert rule["stigs"][0]["id"] == stig_id

    man = json.loads((data / "search" / "manifest.json").read_text(encoding="utf-8"))
    assert man.get("format") == "stigref-search-shards/v1"
    assert man.get("total", 0) >= 3
    from stigref_build.search_index import load_all_documents

    docs = load_all_documents(data / "search")
    types = {d["type"] for d in docs}
    assert types == {"stig", "rule"}
    # gzip shard present
    gz0 = data / "search" / man["shards"][0]["pathGz"]
    assert gz0.is_file()


def test_parse_nested_library_zip(tmp_path: Path):
    """Library zip → nested STIG zip → xccdf.xml."""
    inner_buf_path = tmp_path / "U_Example_OS_V1R3_STIG.zip"
    with zipfile.ZipFile(inner_buf_path, "w") as inner:
        inner.write(FIXTURE, arcname="U_Example_OS_V1R3_Manual_STIG/sample_stig-xccdf.xml")

    library = tmp_path / "U_SRG-STIG_Library_Test.zip"
    with zipfile.ZipFile(library, "w") as outer:
        outer.write(inner_buf_path, arcname=inner_buf_path.name)

    stigs, errors = parse_all(library)
    assert not errors
    assert len(stigs) == 1
    assert stigs[0]["rule_count"] == 2

    meta = write_data_tree(stigs, tmp_path / "out", source_path=library)
    assert meta["counts"]["stigs"] == 1
