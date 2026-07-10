import { describe, it, expect } from "vitest";
import { buildSearchUrl, parseSearchParams } from "./urlState";
import { emptyFilters } from "./search";

describe("urlState", () => {
  it("round-trips query and filters", () => {
    const f = emptyFilters();
    f.type = "rule";
    f.severity = "high";
    f.vendor = "Microsoft";
    f.hasIntune = true;
    f.hasCve = true;
    f.inKev = true;
    const url = buildSearchUrl("spooler", f);
    expect(url).toContain("q=spooler");
    expect(url).toContain("type=rule");
    expect(url).toContain("severity=high");
    expect(url).toContain("vendor=Microsoft");
    expect(url).toContain("intune=1");
    expect(url).toContain("cve=1");
    expect(url).toContain("kev=1");

    const qs = url.includes("?") ? url.slice(url.indexOf("?")) : "";
    const parsed = parseSearchParams(qs);
    expect(parsed.q).toBe("spooler");
    expect(parsed.filters).toEqual(f);
  });

  it("handles empty search", () => {
    const url = buildSearchUrl("", emptyFilters());
    expect(url.endsWith("/") || url.endsWith("/stigref") || url.includes("/stigref/")).toBe(true);
    const parsed = parseSearchParams("");
    expect(parsed.q).toBe("");
    expect(parsed.filters.hasIntune).toBe(false);
  });
});
