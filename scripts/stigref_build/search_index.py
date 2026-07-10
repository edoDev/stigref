"""
Sharded + gzip-compressed search index writer (B-041).

Layout:
  data/search/manifest.json
  data/search/shards/stigs.json[.gz]
  data/search/shards/rules-00.json[.gz] … rules-{N-1}.json[.gz]

Also writes legacy data/search/documents.json for one release cycle (optional).
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Number of rule shards (parallel fetch ~16)
RULE_SHARDS = 16


def _write_shard(
    path: Path, obj: Any, *, write_plain: bool = True
) -> tuple[int, int]:
    """Write gzip always; plain optional (for fallback / tooling)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    gz_path = Path(str(path) + ".gz") if not str(path).endswith(".gz") else path
    if path.suffix == ".json":
        gz_path = path.with_name(path.name + ".gz")
    plain_bytes = 0
    if write_plain:
        path.write_text(text, encoding="utf-8")
        plain_bytes = path.stat().st_size
    with gzip.open(gz_path, "wt", encoding="utf-8", compresslevel=6) as f:
        f.write(text)
    return plain_bytes, gz_path.stat().st_size


def _shard_key(doc_id: str, n: int = RULE_SHARDS) -> int:
    h = hashlib.md5(doc_id.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % n


def _read_json_maybe_gz(path: Path) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    gz = Path(str(path) + ".gz") if not str(path).endswith(".gz") else path
    if path.suffix == ".json":
        gz = path.with_name(path.name + ".gz")
    if gz.is_file():
        with gzip.open(gz, "rt", encoding="utf-8") as f:
            return json.loads(f.read())
    raise FileNotFoundError(path)


def load_all_documents(search_dir: Path) -> list[dict[str, Any]]:
    """Load docs from sharded index or legacy documents.json."""
    search_dir = Path(search_dir)
    man = search_dir / "manifest.json"
    if man.is_file() or (search_dir / "manifest.json.gz").is_file():
        if man.is_file():
            manifest = json.loads(man.read_text(encoding="utf-8"))
        else:
            with gzip.open(search_dir / "manifest.json.gz", "rt", encoding="utf-8") as f:
                manifest = json.loads(f.read())
        docs: list[dict[str, Any]] = []
        for s in manifest.get("shards") or []:
            p = search_dir / s["path"]
            try:
                blob = _read_json_maybe_gz(p)
            except FileNotFoundError:
                continue
            docs.extend(blob.get("documents") or [])
        if docs:
            return docs
    leg = search_dir / "documents.json"
    if leg.is_file() or (search_dir / "documents.json.gz").is_file():
        blob = _read_json_maybe_gz(leg)
        return list(blob.get("documents") or [])
    return []


def write_search_index(
    out_search: Path,
    docs: list[dict[str, Any]],
    *,
    write_legacy_monolith: bool = False,
    write_plain_shards: bool = False,
    rule_shards: int = RULE_SHARDS,
) -> dict[str, Any]:
    """
    Write sharded + gzip search index under out_search (…/data/search).

    By default only **gzip** shards are written (B-041 repo size), plus a small
    plain manifest.json for easy inspection. Frontend prefers .gz via DecompressionStream.
    """
    out_search = Path(out_search)
    shards_dir = out_search / "shards"
    if shards_dir.exists():
        for p in shards_dir.iterdir():
            if p.is_file():
                p.unlink()
    shards_dir.mkdir(parents=True, exist_ok=True)

    stigs: list[dict[str, Any]] = []
    rules_buckets: list[list[dict[str, Any]]] = [[] for _ in range(rule_shards)]
    other: list[dict[str, Any]] = []

    for d in docs:
        t = d.get("type")
        if t == "stig":
            stigs.append(d)
        elif t == "rule":
            key = str(d.get("id") or d.get("full_rule_id") or "")
            rules_buckets[_shard_key(key, rule_shards)].append(d)
        else:
            other.append(d)

    if other:
        rules_buckets[-1].extend(other)

    shard_meta: list[dict[str, Any]] = []

    def emit(name: str, payload: list[dict[str, Any]]) -> None:
        path = shards_dir / f"{name}.json"
        plain, gz = _write_shard(
            path,
            {"documents": payload, "count": len(payload)},
            write_plain=write_plain_shards,
        )
        shard_meta.append(
            {
                "id": name,
                "path": f"shards/{name}.json",
                "pathGz": f"shards/{name}.json.gz",
                "count": len(payload),
                "bytes": plain,
                "bytesGz": gz,
            }
        )
        log.info(
            "Search shard %s: %s docs · plain=%s · gzip %.1f KB",
            name,
            len(payload),
            f"{plain / 1024:.1f} KB" if plain else "skipped",
            gz / 1024,
        )

    emit("stigs", stigs)
    for i, bucket in enumerate(rules_buckets):
        emit(f"rules-{i:02d}", bucket)

    total_plain = sum(s["bytes"] for s in shard_meta)
    total_gz = sum(s["bytesGz"] for s in shard_meta)
    manifest = {
        "version": 1,
        "format": "stigref-search-shards/v1",
        "total": len(docs),
        "ruleShards": rule_shards,
        "preferGzip": True,
        "gzipOnly": not write_plain_shards,
        "shards": shard_meta,
        "totals": {
            "bytes": total_plain,
            "bytesGz": total_gz,
            "ratio": round(total_gz / total_plain, 3) if total_plain else None,
        },
    }
    man_path = out_search / "manifest.json"
    man_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with gzip.open(str(man_path) + ".gz", "wt", encoding="utf-8", compresslevel=6) as f:
        f.write(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n")

    if write_legacy_monolith:
        leg = out_search / "documents.json"
        _write_shard(
            leg,
            {"documents": docs, "total": len(docs)},
            write_plain=True,
        )

    log.info(
        "Search index: %s docs · gzip total %.1f MB%s",
        len(docs),
        total_gz / (1024 * 1024),
        f" · plain {total_plain / (1024 * 1024):.1f} MB" if total_plain else " (gzip-only)",
    )
    return manifest
