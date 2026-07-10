export type LoadState = "idle" | "loading" | "success" | "error";

export interface ReleaseInfo {
  id: string;
  label: string;
  sourceFile?: string | null;
  builtAt?: string | null;
  /** Where catalog files live: "live" = top-level data/, else relative path under data/ */
  storage?: "live" | string;
}

export interface Meta {
  lastUpdated: string;
  builtAt?: string;
  /** Active catalog release id (e.g. 2026-04) — B-021 */
  currentRelease?: string;
  release?: ReleaseInfo;
  releases?: ReleaseInfo[];
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
  sizes?: {
    totalBytes?: number;
    totalFiles?: number;
    totalMB?: number;
    byArea?: Record<string, { bytes?: number; files?: number }>;
    note?: string;
  };
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
  hasAttack?: boolean;
  hasCis?: boolean;
  hasOval?: boolean;
  hasScap?: boolean;
}

export interface SearchFilters {
  type: "" | "stig" | "rule" | "srg";
  severity: string;
  vendor: string;
  hasIntune: boolean;
  hasCve: boolean;
  inKev: boolean;
  hasAttack: boolean;
  hasCis: boolean;
  hasOval: boolean;
  hasScap: boolean;
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
  /** Settings Catalog friendly name (B-013) */
  settingsCatalogName?: string;
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

export interface CisItem {
  id: string;
  title?: string;
  benchmark?: string;
  benchmarkVersion?: string;
  profile?: string;
  product?: string;
  relationship?: string;
  confidence?: string;
  notes?: string;
  source?: string;
  hasLocalExtract?: boolean;
  localDescription?: string;
  localAudit?: string;
  localRemediation?: string;
  localSourceFile?: string;
}

export interface CisPayload {
  status: string;
  items: CisItem[];
  disclaimer?: string;
  localExtractCount?: number;
}

export interface ScapPayload {
  hasOval?: boolean;
  hasScapSignal?: boolean;
  hasOvalInCheckText?: boolean;
  hasOvalSystemOrHref?: boolean;
  hasScapInText?: boolean;
  scapFalsePositiveNote?: boolean;
  checkSystems?: string[];
  checkContentRefs?: Array<{ href?: string; name?: string }>;
  note?: string;
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
  cis?: CisPayload | null;
  scap?: ScapPayload | null;
  checkAutomation?: {
    checkStyle?: string;
    confidence?: string;
    reasons?: string[];
  };
  packageEnrichment?: {
    ckl?: {
      sourceCkl?: string;
      status?: string;
      gpoRefs?: string[];
      intuneRefs?: string[];
      outsideGpoScope?: boolean;
      outsideIntuneScope?: boolean;
      siteSpecific?: boolean;
      comments?: string;
    } | null;
    deviation?: {
      vulnNum?: string;
      category?: string;
      notNativeToIntune?: boolean;
      falsePositiveScap?: boolean;
      explanation?: string;
      cspRegistryPath?: string;
      sheet?: string;
    } | null;
    settingsCatalogProfiles?: Array<{
      name?: string;
      path?: string;
      settingCount?: number;
    }>;
  };
  enrichmentTags?: string[];
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

/** Precomputed Library Observatory payload (data/stats/insights.json) — B-090 */
export interface InsightsKpis {
  stigs?: number;
  rules?: number;
  vendors?: number;
  families?: number;
  stigsWithGpo?: number;
  stigsWithIntunePackage?: number;
  stigsShbRelated?: number;
  rulesWithCve?: number;
  rulesWithKev?: number;
  rulesWithCis?: number;
  rulesWithOval?: number;
  rulesWithScap?: number;
  rulesWithIntuneMap?: number;
  rulesWithAttack?: number;
  uniqueCcis?: number;
  intuneProducts?: number;
  searchTransferBytesGz?: number;
  searchTransferMBGz?: number;
  dataTotalMB?: number;
  parseErrors?: number;
}

export interface InsightsSevBucket {
  total?: number;
  mapped?: number;
  pct?: number;
}

export interface InsightsIntuneProduct {
  product: string;
  stigId?: string;
  stigName?: string;
  rules?: number;
  mappedRules?: number;
  settings?: number;
  coveragePct?: number;
  severityCoverage?: {
    high?: InsightsSevBucket;
    medium?: InsightsSevBucket;
    low?: InsightsSevBucket;
  };
  confidence?: { high?: number; medium?: number; low?: number };
  kinds?: Record<string, number>;
  unmappedCatI?: Array<{ id: string; title: string }>;
}

export interface InsightsDoc {
  format?: string;
  generatedAt?: string;
  releaseId?: string;
  disclaimers?: Record<string, string>;
  kpis: InsightsKpis;
  severity?: {
    high?: number;
    medium?: number;
    low?: number;
    unknown?: number;
  };
  vendors?: Array<{ name: string; stigs: number; rules: number }>;
  roles?: Array<{ role: string; stigs: number; rules: number }>;
  landscape?: Array<{
    vendor: string;
    family: string;
    stigs: number;
    rules: number;
    hasGpo?: boolean;
    hasIntunePackage?: boolean;
    shbRelated?: boolean;
  }>;
  automation?: {
    stigs?: {
      gpoPackage?: number;
      intunePackage?: number;
      both?: number;
      neither?: number;
      shb?: number;
      manualOrPlatform?: number;
    };
    rules?: Record<string, number | Record<string, number>>;
  };
  intuneProducts?: InsightsIntuneProduct[];
  cis?: {
    rulesWithCis?: number;
    totalMappedRules?: number;
    mapFiles?: number;
    byProduct?: Array<{ product: string; rules: number }>;
    topCisIds?: Array<{ id: string; rules: number }>;
    disclaimer?: string;
  };
  cci?: {
    uniqueCcis?: number;
    rulesWithCci?: number;
    top?: Array<{ id: string; ruleCount: number }>;
  };
  attack?: {
    rulesWithAttack?: number;
    techniques?: Array<{ id: string; name?: string; ruleCount: number }>;
    disclaimer?: string;
  };
  kev?: {
    catalogCount?: number;
    catalogVersion?: string;
    dateReleased?: string;
    fetchedAt?: string;
    rulesWithKev?: number;
    ransomwareKnown?: number;
    byYear?: Array<{ year: string; count: number }>;
    topVendors?: Array<{ vendor: string; count: number }>;
    disclaimer?: string;
  };
  health?: {
    builtAt?: string;
    lastUpdated?: string;
    currentRelease?: string;
    sourceFile?: string;
    sourceSha256?: string;
    generator?: string;
    parseErrors?: number;
    totalMB?: number;
    totalFiles?: number;
    searchBytesGz?: number;
    searchShards?: number;
    counts?: Record<string, number>;
  };
  delta?: {
    available?: boolean;
    note?: string;
    releases?: Array<{ id?: string; label?: string }>;
  };
  scorecards?: Array<{
    stigId?: string;
    name?: string;
    vendor?: string;
    family?: string;
    ruleCount?: number;
    severity?: { high?: number; medium?: number; low?: number };
    hasGpoPackage?: boolean;
    hasIntunePackage?: boolean;
    shbRelated?: boolean;
    intuneCoveragePct?: number | null;
    intuneProduct?: string | null;
    rulesWithCis?: number;
    rulesWithScap?: number;
  }>;
}
