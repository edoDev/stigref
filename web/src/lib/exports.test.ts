import { describe, it, expect } from "vitest";
import { ruleExportCsv, ruleExportMarkdown, ruleStigCisCompareMarkdown } from "./exports";
import type { RuleDetail } from "./types";

const sample: RuleDetail = {
  id: "SV-1",
  full_rule_id: "SV-253284r1_rule",
  rule_id: "SV-253284",
  rule_revision: "1",
  group_id: "V-1",
  group_title: "",
  title: "SEHOP must be enabled",
  severity: "high",
  description: "",
  check: "Check SEHOP",
  fix: "Enable SEHOP",
  ccis: ["CCI-1"],
  cves: [],
  metadata: {},
  stigs: [],
  stig_ids: [],
  cis: {
    status: "mapped",
    items: [
      {
        id: "18.9.95.1",
        title: "Ensure SEHOP is enabled",
        profile: "Level_1",
        relationship: "equivalent",
        confidence: "high",
        benchmark: "CIS Windows 11",
        notes: "Same control intent",
      },
    ],
    disclaimer: "Assistive only",
  },
};

describe("exports", () => {
  it("csv includes cis columns", () => {
    const csv = ruleExportCsv(sample);
    expect(csv).toContain("cis_id");
    expect(csv).toContain("18.9.95.1");
    expect(csv).toContain("SV-253284r1_rule");
  });

  it("markdown includes both check and cis", () => {
    const md = ruleExportMarkdown(sample);
    expect(md).toContain("## STIG Check");
    expect(md).toContain("## CIS Benchmark crosswalk");
    expect(md).toContain("18.9.95.1");
  });

  it("compare markdown has side-by-side", () => {
    const md = ruleStigCisCompareMarkdown(sample);
    expect(md).toContain("STIG ↔ CIS");
    expect(md).toContain("Check SEHOP");
  });
});
