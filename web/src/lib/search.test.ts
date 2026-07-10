import { describe, it, expect, beforeEach } from "vitest";
import {
  applyFilters,
  buildSearchIndex,
  emptyFilters,
  isSearchReady,
  search,
  uniqueVendorsFromIndex,
} from "./search";
import type { SearchDoc } from "./types";

function doc(partial: Partial<SearchDoc> & Pick<SearchDoc, "id" | "type" | "title">): SearchDoc {
  return {
    body: "",
    route: `/x/${partial.id}`,
    ...partial,
  };
}

const SAMPLE: SearchDoc[] = [
  doc({
    id: "r1",
    type: "rule",
    title: "Disable Print Spooler",
    full_rule_id: "SV-12345r1_rule",
    severity: "high",
    vendor: "Microsoft",
    hasIntune: true,
    hasCve: true,
    inKev: true,
    cves: ["CVE-2021-34527"],
    body: "print spooler service",
  }),
  doc({
    id: "r2",
    type: "rule",
    title: "Configure audit log size",
    full_rule_id: "SV-99999r1_rule",
    severity: "medium",
    vendor: "Microsoft",
    hasIntune: false,
    hasCve: false,
    inKev: false,
    body: "event log",
  }),
  doc({
    id: "s1",
    type: "stig",
    title: "Windows 11 STIG",
    vendor: "Microsoft",
    body: "windows client",
  }),
  doc({
    id: "s2",
    type: "stig",
    title: "RHEL 9 STIG",
    vendor: "Red Hat",
    body: "linux",
  }),
];

beforeEach(() => {
  buildSearchIndex(SAMPLE);
});

describe("buildSearchIndex / isSearchReady", () => {
  it("marks search ready after build", () => {
    expect(isSearchReady()).toBe(true);
  });
});

describe("applyFilters", () => {
  it("filters by type and severity", () => {
    const f = emptyFilters();
    f.type = "rule";
    f.severity = "high";
    const out = applyFilters(SAMPLE, f);
    expect(out).toHaveLength(1);
    expect(out[0].id).toBe("r1");
  });

  it("filters hasIntune / hasCve / inKev", () => {
    const f = emptyFilters();
    f.hasIntune = true;
    f.hasCve = true;
    f.inKev = true;
    expect(applyFilters(SAMPLE, f).map((d) => d.id)).toEqual(["r1"]);
  });

  it("filters by vendor", () => {
    const f = emptyFilters();
    f.vendor = "Red Hat";
    expect(applyFilters(SAMPLE, f).map((d) => d.id)).toEqual(["s2"]);
  });
});

describe("search", () => {
  it("returns empty when query and filters empty is not this function's job — still searches pool", () => {
    // search with empty q returns filtered pool slice
    const out = search("", 10, emptyFilters());
    expect(out.length).toBe(SAMPLE.length);
  });

  it("prefers rule-id hits", () => {
    const out = search("SV-12345", 10);
    expect(out[0]?.full_rule_id).toBe("SV-12345r1_rule");
  });

  it("finds by title/body text", () => {
    const out = search("spooler", 10);
    expect(out.some((d) => d.id === "r1")).toBe(true);
  });

  it("combines text search with filters", () => {
    const f = emptyFilters();
    f.type = "rule";
    f.severity = "medium";
    const out = search("audit", 10, f);
    expect(out.map((d) => d.id)).toEqual(["r2"]);
  });
});

describe("uniqueVendorsFromIndex", () => {
  it("lists sorted unique vendors", () => {
    expect(uniqueVendorsFromIndex()).toEqual(["Microsoft", "Red Hat"]);
  });
});
