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
    hasAttack: false,
    hasCis: false,
  };
}

function isSrgDoc(d: SearchDoc): boolean {
  const t = `${d.title || ""} ${d.body || ""}`.toLowerCase();
  return (
    t.includes("requirements guide") ||
    /\bsrg\b/.test(t) ||
    (d.type === "stig" && t.includes("security requirements guide"))
  );
}

export function applyFilters(docs: SearchDoc[], f: SearchFilters): SearchDoc[] {
  return docs.filter((d) => {
    if (f.type === "srg") {
      if (d.type !== "stig" || !isSrgDoc(d)) return false;
    } else if (f.type === "stig") {
      if (d.type !== "stig" || isSrgDoc(d)) return false;
    } else if (f.type && d.type !== f.type) {
      return false;
    }
    if (f.severity && (d.severity || "").toLowerCase() !== f.severity.toLowerCase())
      return false;
    if (f.vendor && (d.vendor || "") !== f.vendor) return false;
    if (f.hasIntune && !d.hasIntune) return false;
    if (f.hasCve && !d.hasCve) return false;
    if (f.inKev && !d.inKev) return false;
    if (f.hasAttack && !d.hasAttack) return false;
    if (f.hasCis && !d.hasCis) return false;
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
      "hasAttack",
      "hasCis",
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

  const upper = q.toUpperCase().replace(/\s+/g, "");
  const idHits: SearchDoc[] = [];
  // B-031: tolerate missing "rN_rule" suffix and minor typos on SV-/V- ids
  const bare = upper.replace(/R\d+_RULE$/i, "").replace(/_RULE$/i, "");
  for (const doc of allDocs) {
    if (doc.type !== "rule") continue;
    const rid = (doc.full_rule_id || "").toUpperCase();
    const ridBare = rid.replace(/R\d+_RULE$/i, "").replace(/_RULE$/i, "");
    if (
      rid === upper ||
      rid.startsWith(upper) ||
      rid.includes(upper) ||
      ridBare === bare ||
      ridBare.startsWith(bare) ||
      (bare.length >= 6 && ridBare.includes(bare)) ||
      (bare.length >= 8 && levenshtein(ridBare, bare) <= 2)
    ) {
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

/** Small Levenshtein for rule-id typo tolerance (B-031). */
export function levenshtein(a: string, b: string): number {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  const row = new Array(b.length + 1);
  for (let j = 0; j <= b.length; j++) row[j] = j;
  for (let i = 1; i <= a.length; i++) {
    let prev = i - 1;
    row[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const cur = row[j];
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      row[j] = Math.min(row[j] + 1, row[j - 1] + 1, prev + cost);
      prev = cur;
    }
  }
  return row[b.length];
}
