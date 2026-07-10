import { describe, it, expect } from "vitest";
import {
  insightsBoardMarkdown,
  insightsIntuneCsv,
  insightsScorecardsCsv,
} from "./insightsExport";
import type { InsightsDoc } from "./types";

const sample: InsightsDoc = {
  format: "stigref-insights/v1",
  generatedAt: "2026-07-10T00:00:00Z",
  releaseId: "2026-04",
  disclaimers: {
    general: "Test disclaimer",
    intune: "Intune note",
    kev: "KEV note",
  },
  kpis: {
    stigs: 2,
    rules: 10,
    vendors: 1,
    families: 1,
    stigsWithGpo: 1,
    stigsWithIntunePackage: 1,
    rulesWithIntuneMap: 3,
    rulesWithCis: 2,
    uniqueCcis: 4,
    searchTransferMBGz: 2.5,
  },
  severity: { high: 1, medium: 8, low: 1, unknown: 0 },
  automation: {
    stigs: { both: 1, gpoPackage: 0, intunePackage: 0, neither: 1, shb: 1 },
  },
  intuneProducts: [
    {
      product: "windows-11",
      stigName: "Windows 11 STIG",
      rules: 10,
      mappedRules: 3,
      coveragePct: 30,
      settings: 5,
      severityCoverage: { high: { total: 2, mapped: 1, pct: 50 } },
      confidence: { high: 2, medium: 2, low: 1 },
      unmappedCatI: [{ id: "SV-1_rule", title: "Enable thing" }],
    },
  ],
  scorecards: [
    {
      vendor: "Microsoft",
      family: "windows-11",
      name: "Windows 11 STIG",
      ruleCount: 10,
      severity: { high: 1, medium: 8, low: 1 },
      hasGpoPackage: true,
      hasIntunePackage: true,
      shbRelated: true,
      intuneCoveragePct: 30,
      rulesWithCis: 2,
      rulesWithScap: 0,
    },
  ],
  kev: { catalogCount: 100 },
};

describe("insightsExport", () => {
  it("builds board markdown with KPIs and products", () => {
    const md = insightsBoardMarkdown(sample, "https://example.com");
    expect(md).toContain("Library Observatory");
    expect(md).toContain("windows-11");
    expect(md).toContain("30%");
    expect(md).toContain("SV-1_rule");
  });

  it("builds intune CSV", () => {
    const csv = insightsIntuneCsv(sample);
    expect(csv.split("\n")[0]).toContain("coveragePct");
    expect(csv).toContain("windows-11");
  });

  it("builds scorecards CSV", () => {
    const csv = insightsScorecardsCsv(sample);
    expect(csv).toContain("Microsoft");
    expect(csv).toContain("windows-11");
  });
});
