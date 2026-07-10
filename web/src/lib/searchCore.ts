/**
 * Pure search helpers + MiniSearch engine factory.
 * Used by main-thread fallback and the Web Worker (B-040).
 */
import MiniSearch from "minisearch";
import type { SearchDoc, SearchFilters } from "./types";

export function emptyFilters(): SearchFilters {
  return {
    type: "",
    severity: "",
    vendor: "",
    hasIntune: false,
    hasCve: false,
    inKev: false,
  };
}

export function applyFilters(docs: SearchDoc[], f: SearchFilters): SearchDoc[] {
  return docs.filter((d) => {
    if (f.type && d.type !== f.type) return false;
    if (f.severity && (d.severity || "").toLowerCase() !== f.severity.toLowerCase())
      return false;
    if (f.vendor && (d.vendor || "") !== f.vendor) return false;
    if (f.hasIntune && !d.hasIntune) return false;
    if (f.hasCve && !d.hasCve) return false;
    if (f.inKev && !d.inKev) return false;
    return true;
  });
}

export function createEngine(docs: SearchDoc[]): MiniSearch<SearchDoc> {
  const engine = new MiniSearch<SearchDoc>({
    fields: ["title", "body", "full_rule_id", "stig_names", "cves", "ccis"],
    storeFields: [
      "id",
      "type",
      "title",
      "body",
      "route",
      "severity",
      "full_rule_id",
      "group_id",
      "stig_names",
      "version",
      "release",
      "release_date",
      "vendor",
      "roles",
      "hasIntune",
      "hasCve",
      "inKev",
      "cves",
      "ccis",
    ],
    searchOptions: {
      boost: { title: 3, full_rule_id: 4, body: 1, cves: 5 },
      fuzzy: 0.15,
      prefix: true,
    },
    extractField: (doc, field) => {
      if (field === "stig_names") return (doc.stig_names || []).join(" ");
      if (field === "cves") return (doc.cves || []).join(" ");
      if (field === "ccis") return (doc.ccis || []).join(" ");
      const v = (doc as Record<string, unknown>)[field];
      return v == null ? "" : String(v);
    },
  });
  engine.addAll(docs);
  return engine;
}

export function searchWithEngine(
  engine: MiniSearch<SearchDoc> | null,
  allDocs: SearchDoc[],
  docsById: Map<string, SearchDoc>,
  query: string,
  limit = 40,
  filters?: SearchFilters,
): SearchDoc[] {
  if (!engine) return [];
  const f = filters || emptyFilters();
  const q = query.trim();

  if (!q) {
    return applyFilters(allDocs, f).slice(0, limit);
  }

  const upper = q.toUpperCase();
  const idHits: SearchDoc[] = [];
  for (const doc of allDocs) {
    if (doc.type !== "rule") continue;
    const rid = (doc.full_rule_id || "").toUpperCase();
    if (rid === upper || rid.startsWith(upper) || rid.includes(upper)) {
      idHits.push(doc);
      if (idHits.length >= limit) break;
    }
  }

  const hits = engine.search(q, { combineWith: "AND" });
  const fuzzy: SearchDoc[] = [];
  for (const hit of hits) {
    const doc = docsById.get(String(hit.id));
    if (doc) fuzzy.push(doc);
  }

  const seen = new Set<string>();
  const merged: SearchDoc[] = [];
  for (const d of [...idHits, ...fuzzy]) {
    if (seen.has(d.id)) continue;
    seen.add(d.id);
    merged.push(d);
  }

  return applyFilters(merged, f).slice(0, limit);
}

export function uniqueVendors(docs: SearchDoc[]): string[] {
  const s = new Set<string>();
  for (const d of docs) {
    if (d.vendor) s.add(d.vendor);
  }
  return [...s].sort();
}
