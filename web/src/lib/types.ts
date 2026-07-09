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
    rulesWithCve?: number;
    rulesWithKev?: number;
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
  group_id?: string;
  ccis?: string[];
  cves?: string[];
  stig_names?: string[];
  version?: string;
  release?: string;
  release_date?: string;
  vendor?: string;
  roles?: string[];
  tags?: string[];
  hasIntune?: boolean;
  hasCve?: boolean;
  inKev?: boolean;
}

export interface SearchFilters {
  type: "" | "stig" | "rule";
  severity: string;
  vendor: string;
  hasIntune: boolean;
  hasCve: boolean;
  inKev: boolean;
}

export interface StigIndexEntry {
  id: string;
  name: string;
  version: string;
  release: string;
  release_date: string;
  rule_count: number;
  family?: string;
  vendor?: string;
  roles?: string[];
  tags?: string[];
  quicklink_id?: string | null;
  hasGpoPackage?: boolean;
  hasIntunePackage?: boolean;
  shbRelated?: boolean;
  manualOrPlatformNative?: boolean;
}

export interface StigAutomation {
  hasGpoPackage?: boolean;
  hasIntunePackage?: boolean;
  gpoProducts?: string[];
  intuneProfiles?: Array<{ name: string; category?: string; path?: string }>;
  shbRelated?: boolean;
  manualOrPlatformNative?: boolean;
  platformKind?: string | null;
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
  family?: string;
  vendor?: string;
  roles?: string[];
  tags?: string[];
  quicklink_id?: string | null;
  automation?: StigAutomation;
}

export interface QuickLink {
  id: string;
  label: string;
  stigId: string | null;
  stigName: string | null;
  found: boolean;
}

export interface TagsCatalog {
  vendors: string[];
  roles: string[];
  tags: string[];
  quickLinks: QuickLink[];
  filterHints?: {
    roles?: string[];
    special?: Array<{ id: string; label: string; tag: string }>;
  };
}

export interface IntuneSuggestion {
  cspId?: string;
  title?: string;
  area?: string;
  name?: string;
  kind?: string;
  scope?: string[];
  omaUri?: string;
  dataType?: string;
  value?: string | null;
  confidence?: string;
  rationale?: string;
  learnUrl?: string;
  description?: string;
  source?: string;
}

export interface IntunePayload {
  suggestions: IntuneSuggestion[];
  status: string;
  policySearchUrl?: string;
  message?: string | null;
  multiOption?: boolean;
}

export interface ThreatCve {
  id: string;
  inKev?: boolean;
  nvdUrl?: string;
  kevUrl?: string | null;
  cvss?: { version?: string; score?: number; severity?: string };
}

export interface ThreatPayload {
  status: string;
  cves: ThreatCve[];
  inKev?: boolean;
  attack?: Array<{
    techniqueId: string;
    name: string;
    url: string;
    confidence?: string;
    source?: string;
  }>;
  references?: Array<{
    type: string;
    title: string;
    url: string;
    publisher?: string;
    date?: string;
  }>;
  iocs?: Array<{
    type: string;
    value: string;
    sourceUrl?: string;
    note?: string;
  }>;
  disclaimer?: string;
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
  intune?: IntunePayload | null;
  threat?: ThreatPayload | null;
  checkAutomation?: {
    checkStyle?: string;
    confidence?: string;
    reasons?: string[];
  };
}

export interface IntuneProductIndex {
  products: Array<{
    product: string;
    stigId?: string;
    stigName?: string;
    settings?: number;
    mappedRules?: number;
    rules?: number;
    path?: string;
  }>;
  total: number;
}
