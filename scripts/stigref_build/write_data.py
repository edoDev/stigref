"""Write stigref static data/ tree from parsed STIG dicts."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stigref_build import __version__
from stigref_build.ids import rule_path_id
from stigref_build.intune_suggest import attach_intune_to_stigs, load_csp_catalog
from stigref_build.tags import build_quick_links, enrich_stig, load_curated

log = logging.getLogger(__name__)

SEARCH_BODY_MAX = 400


def _sha256_file(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _truncate(text: str, max_len: int = SEARCH_BODY_MAX) -> str:
    text = " ".join((text or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def merge_rules_across_stigs(stigs: list[dict]) -> dict[str, dict]:
    """
    Index rules by full_rule_id. If the same rule appears in multiple STIGs,
    merge stig_ids lists.
    """
    by_id: dict[str, dict] = {}
    for stig in stigs:
        for rule in stig.get("rules") or []:
            rid = rule["full_rule_id"]
            if rid not in by_id:
                # Shallow copy so we can mutate stig_ids
                item = dict(rule)
                item["stig_ids"] = list(rule.get("stig_ids") or [stig["id"]])
                item["stigs"] = [
                    {
                        "id": stig["id"],
                        "name": stig["name"],
                        "version": stig["version"],
                        "release": stig["release"],
                    }
                ]
                by_id[rid] = item
            else:
                existing = by_id[rid]
                if stig["id"] not in existing["stig_ids"]:
                    existing["stig_ids"].append(stig["id"])
                    existing["stigs"].append(
                        {
                            "id": stig["id"],
                            "name": stig["name"],
                            "version": stig["version"],
                            "release": stig["release"],
                        }
                    )
    return by_id


def build_search_documents(
    stigs: list[dict], rules_by_id: dict[str, dict]
) -> list[dict]:
    docs: list[dict] = []
    for stig in stigs:
        docs.append(
            {
                "id": f"stig:{stig['id']}",
                "type": "stig",
                "title": stig["name"],
                "body": _truncate(
                    " ".join(
                        [
                            stig["name"],
                            stig.get("description") or "",
                            f"V{stig['version']}R{stig['release']}",
                            stig.get("vendor") or "",
                            " ".join(stig.get("roles") or []),
                            " ".join(stig.get("tags") or []),
                        ]
                    )
                ),
                "route": f"/stigs/{stig['id']}",
                "version": stig["version"],
                "release": stig["release"],
                "release_date": stig.get("release_date") or "",
                "vendor": stig.get("vendor") or "",
                "roles": stig.get("roles") or [],
                "tags": stig.get("tags") or [],
            }
        )

    for rule in rules_by_id.values():
        body = _truncate(
            " ".join(
                [
                    rule.get("full_rule_id") or "",
                    rule.get("title") or "",
                    rule.get("check") or "",
                    rule.get("group_id") or "",
                    " ".join(rule.get("ccis") or []),
                ]
            )
        )
        docs.append(
            {
                "id": f"rule:{rule['full_rule_id']}",
                "type": "rule",
                "title": rule.get("title") or rule["full_rule_id"],
                "body": body,
                "route": f"/rules/{rule_path_id(rule['full_rule_id'])}",
                "severity": rule.get("severity") or "",
                "full_rule_id": rule["full_rule_id"],
                "stig_names": [s["name"] for s in rule.get("stigs") or []],
            }
        )
    return docs


def write_data_tree(
    stigs: list[dict],
    out_dir: str | Path,
    *,
    source_path: Path | None = None,
    source_filename: str | None = None,
    clean: bool = True,
    errors: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Write the full data/ layout. Returns the meta dict written.
    """
    out = Path(out_dir)
    if clean and out.exists():
        # Only remove known subtrees to avoid deleting unrelated files
        for sub in (
            "stigs",
            "rules",
            "search",
            "controls",
            "ccis",
            "tags",
            "families",
            "intune",
            "csp",
        ):
            p = out / sub
            if p.exists():
                shutil.rmtree(p)
        meta_path = out / "meta.json"
        if meta_path.exists():
            meta_path.unlink()

    out.mkdir(parents=True, exist_ok=True)

    curated = load_curated()
    stigs = [enrich_stig(s, curated) for s in stigs]
    # Intune CSP suggestions (quick-link products) during STIG processing
    csp_catalog = load_csp_catalog()
    stigs, intune_exports = attach_intune_to_stigs(stigs, catalog=csp_catalog)
    rules_by_id = merge_rules_across_stigs(stigs)

    # STIG index + detail (detail includes rule summaries, not always full text)
    stig_index: list[dict] = []
    for stig in sorted(
        stigs, key=lambda s: (s.get("release_date") or "", s["name"]), reverse=True
    ):
        summaries = [
            {
                "id": r["full_rule_id"],
                "full_rule_id": r["full_rule_id"],
                "title": r.get("title") or "",
                "severity": r.get("severity") or "",
                "group_id": r.get("group_id") or "",
            }
            for r in stig.get("rules") or []
        ]
        detail = {
            "id": stig["id"],
            "name": stig["name"],
            "description": stig.get("description") or "",
            "version": stig["version"],
            "release": stig["release"],
            "release_date": stig.get("release_date") or "",
            "rule_count": len(summaries),
            "rules": summaries,
            "source": stig.get("source") or "",
            "family": stig.get("family") or "",
            "vendor": stig.get("vendor") or "",
            "roles": stig.get("roles") or [],
            "tags": stig.get("tags") or [],
            "quicklink_id": stig.get("quicklink_id"),
        }
        _write_json(out / "stigs" / "by-id" / f"{stig['id']}.json", detail)
        stig_index.append(
            {
                "id": stig["id"],
                "name": stig["name"],
                "version": stig["version"],
                "release": stig["release"],
                "release_date": stig.get("release_date") or "",
                "rule_count": len(summaries),
                "family": stig.get("family") or "",
                "vendor": stig.get("vendor") or "",
                "roles": stig.get("roles") or [],
                "tags": stig.get("tags") or [],
                "quicklink_id": stig.get("quicklink_id"),
            }
        )

    _write_json(out / "stigs" / "index.json", {"stigs": stig_index, "total": len(stig_index)})

    # Facets + quick links for UI filters
    vendors = sorted({s["vendor"] for s in stig_index if s.get("vendor")})
    roles = sorted({r for s in stig_index for r in (s.get("roles") or [])})
    tag_set = sorted({t for s in stig_index for t in (s.get("tags") or [])})
    quick_links = build_quick_links(stigs, curated)
    _write_json(
        out / "tags" / "catalog.json",
        {
            "vendors": vendors,
            "roles": roles,
            "tags": tag_set,
            "quickLinks": quick_links,
            "filterHints": {
                "roles": ["server", "workstation", "browser", "mobile", "database", "network", "cloud", "application", "other"],
                "special": [
                    {"id": "intune", "label": "Intune-related", "tag": "intune"},
                    {"id": "intune-companion", "label": "Intune companion", "tag": "intune-companion"},
                    {"id": "gpo-companion", "label": "GPO companion", "tag": "gpo-companion"},
                ],
            },
        },
    )

    # Family map (foundation for multi-release history)
    families: dict[str, list[dict]] = {}
    for s in stig_index:
        fam = s.get("family") or "unknown"
        families.setdefault(fam, []).append(
            {
                "id": s["id"],
                "name": s["name"],
                "version": s["version"],
                "release": s["release"],
                "release_date": s.get("release_date") or "",
            }
        )
    _write_json(
        out / "families" / "index.json",
        {
            "families": [
                {"family": k, "versions": v, "count": len(v)}
                for k, v in sorted(families.items(), key=lambda kv: kv[0])
            ],
            "total": len(families),
        },
    )

    # Full rule detail files
    for rid, rule in rules_by_id.items():
        path_id = rule_path_id(rid)
        detail = {
            "id": rid,
            "full_rule_id": rid,
            "rule_id": rule.get("rule_id") or "",
            "rule_revision": rule.get("rule_revision") or "",
            "group_id": rule.get("group_id") or "",
            "group_title": rule.get("group_title") or "",
            "title": rule.get("title") or "",
            "severity": rule.get("severity") or "",
            "description": rule.get("description") or "",
            "check": rule.get("check") or "",
            "fix": rule.get("fix") or "",
            "ccis": rule.get("ccis") or [],
            "cves": rule.get("cves") or [],
            "metadata": rule.get("metadata") or {},
            "stigs": rule.get("stigs") or [],
            "stig_ids": rule.get("stig_ids") or [],
            "intune": rule.get("intune"),
        }
        _write_json(out / "rules" / "by-id" / f"{path_id}.json", detail)

    # CSP catalog snapshot + product-level Intune export packages
    _write_json(
        out / "csp" / "catalog.json",
        {
            "version": csp_catalog.get("version"),
            "sourceNote": csp_catalog.get("sourceNote"),
            "learnPolicyIndex": csp_catalog.get("learnPolicyIndex"),
            "entries": csp_catalog.get("entries") or [],
            "count": len(csp_catalog.get("entries") or []),
        },
    )
    for exp in intune_exports:
        product = exp.get("product") or "unknown"
        _write_json(out / "intune" / "products" / f"{product}.json", exp)
    _write_json(
        out / "intune" / "index.json",
        {
            "products": [
                {
                    "product": e.get("product"),
                    "stigId": (e.get("stig") or {}).get("id"),
                    "stigName": (e.get("stig") or {}).get("name"),
                    "settings": (e.get("counts") or {}).get("settings"),
                    "mappedRules": (e.get("counts") or {}).get("mappedRules"),
                    "rules": (e.get("counts") or {}).get("rules"),
                    "path": f"intune/products/{e.get('product')}.json",
                }
                for e in intune_exports
            ],
            "total": len(intune_exports),
        },
    )

    docs = build_search_documents(stigs, rules_by_id)
    _write_json(out / "search" / "documents.json", {"documents": docs, "total": len(docs)})

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    # Prefer newest STIG release_date as content lastUpdated when available
    dates = [s.get("release_date") for s in stigs if s.get("release_date")]
    content_updated = max(dates) if dates else now[:10]

    src_name = source_filename
    if src_name is None and source_path is not None:
        src_name = source_path.name

    meta = {
        "lastUpdated": content_updated
        if "T" in str(content_updated)
        else f"{content_updated}T00:00:00Z"
        if len(str(content_updated)) == 10
        else now,
        "builtAt": now,
        "source": {
            "filename": src_name,
            "sha256": _sha256_file(source_path) if source_path else None,
            "urlHint": "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/",
        },
        "counts": {
            "stigs": len(stigs),
            "rules": len(rules_by_id),
            "controls": 0,
            "ccis": 0,
            "searchDocuments": len(docs),
        },
        "parseErrors": len(errors or []),
        "generator": f"stigref-build {__version__}",
    }
    if errors:
        meta["errors"] = errors[:50]  # cap noise in meta

    _write_json(out / "meta.json", meta)
    log.info(
        "Wrote data to %s (%s stigs, %s rules, %s search docs)",
        out,
        meta["counts"]["stigs"],
        meta["counts"]["rules"],
        meta["counts"]["searchDocuments"],
    )
    return meta
