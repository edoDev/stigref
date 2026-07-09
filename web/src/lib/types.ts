export type LoadState = "idle" | "loading" | "success" | "error";

export interface Meta {
  lastUpdated: string;
  builtAt?: string;
  source?: {
    filename?: string | null;
    sha256?: string | null;
    urlHint?: string;
  };
  counts?: {
    stigs?: number;
    rules?: number;
    controls?: number;
    ccis?: number;
    searchDocuments?: number;
  };
  parseErrors?: number;
  generator?: string;
}

export interface SearchDoc {
  id: string;
  type: "stig" | "rule" | "control" | "cci" | string;
  title: string;
  body: string;
  route: string;
  severity?: string;
  full_rule_id?: string;
  stig_names?: string[];
  version?: string;
  release?: string;
  release_date?: string;
}

export interface StigIndexEntry {
  id: string;
  name: string;
  version: string;
  release: string;
  release_date: string;
  rule_count: number;
}

export interface StigDetail {
  id: string;
  name: string;
  description: string;
  version: string;
  release: string;
  release_date: string;
  rule_count: number;
  rules: Array<{
    id: string;
    full_rule_id: string;
    title: string;
    severity: string;
    group_id: string;
  }>;
  source?: string;
}

export interface RuleDetail {
  id: string;
  full_rule_id: string;
  rule_id: string;
  rule_revision: string;
  group_id: string;
  group_title: string;
  title: string;
  severity: string;
  description: string;
  check: string;
  fix: string;
  ccis: string[];
  cves: string[];
  metadata: Record<string, unknown>;
  stigs: Array<{
    id: string;
    name: string;
    version: string;
    release: string;
  }>;
  stig_ids: string[];
}
