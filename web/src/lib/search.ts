import MiniSearch from "minisearch";
import type { SearchDoc } from "./types";

let engine: MiniSearch<SearchDoc> | null = null;
let docsById = new Map<string, SearchDoc>();

export function isSearchReady(): boolean {
  return engine !== null;
}

export function buildSearchIndex(docs: SearchDoc[]): void {
  docsById = new Map(docs.map((d) => [d.id, d]));
  engine = new MiniSearch<SearchDoc>({
    fields: ["title", "body", "full_rule_id", "stig_names"],
    storeFields: [
      "id",
      "type",
      "title",
      "body",
      "route",
      "severity",
      "full_rule_id",
      "stig_names",
      "version",
      "release",
      "release_date",
    ],
    searchOptions: {
      boost: { title: 3, full_rule_id: 4, body: 1 },
      fuzzy: 0.15,
      prefix: true,
    },
    extractField: (doc, field) => {
      if (field === "stig_names") {
        return (doc.stig_names || []).join(" ");
      }
      const v = (doc as Record<string, unknown>)[field];
      return v == null ? "" : String(v);
    },
  });
  engine.addAll(docs);
}

export function search(query: string, limit = 40): SearchDoc[] {
  if (!engine) return [];
  const q = query.trim();
  if (!q) return [];
  const hits = engine.search(q, { combineWith: "AND" });
  const out: SearchDoc[] = [];
  for (const hit of hits.slice(0, limit)) {
    const doc = docsById.get(String(hit.id));
    if (doc) out.push(doc);
  }
  return out;
}

/** Fast path: exact / prefix match on rule ids even before fuzzy search. */
export function searchPreferRuleId(query: string, limit = 40): SearchDoc[] {
  const q = query.trim();
  if (!q) return [];
  const upper = q.toUpperCase();
  const idHits: SearchDoc[] = [];
  if (engine) {
    for (const doc of docsById.values()) {
      if (doc.type !== "rule") continue;
      const rid = (doc.full_rule_id || "").toUpperCase();
      if (rid === upper || rid.startsWith(upper) || rid.includes(upper)) {
        idHits.push(doc);
        if (idHits.length >= limit) break;
      }
    }
  }
  if (idHits.length >= 5) return idHits.slice(0, limit);
  const fuzzy = search(q, limit);
  const seen = new Set(idHits.map((d) => d.id));
  for (const d of fuzzy) {
    if (!seen.has(d.id)) {
      idHits.push(d);
      seen.add(d.id);
    }
    if (idHits.length >= limit) break;
  }
  return idHits;
}
