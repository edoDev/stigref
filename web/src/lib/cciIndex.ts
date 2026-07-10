/** Build CCI → rules index from search documents (B-027) */

import type { SearchDoc } from "./types";

export interface CciEntry {
  cci: string;
  rules: Array<{ id: string; title: string; severity?: string }>;
  count: number;
}

export function buildCciIndex(docs: SearchDoc[]): CciEntry[] {
  const map = new Map<string, CciEntry>();
  for (const d of docs) {
    if (d.type !== "rule") continue;
    for (const raw of d.ccis || []) {
      const cci = String(raw).toUpperCase().trim();
      if (!cci.startsWith("CCI-")) continue;
      let e = map.get(cci);
      if (!e) {
        e = { cci, rules: [], count: 0 };
        map.set(cci, e);
      }
      const rid = d.full_rule_id || d.id;
      if (!e.rules.some((r) => r.id === rid)) {
        e.rules.push({
          id: rid,
          title: d.title || rid,
          severity: d.severity,
        });
        e.count = e.rules.length;
      }
    }
  }
  return [...map.values()].sort((a, b) => a.cci.localeCompare(b.cci));
}
