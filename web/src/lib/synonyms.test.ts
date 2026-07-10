import { describe, it, expect } from "vitest";
import { alternateQueries } from "./synonyms";

describe("synonyms", () => {
  it("expands rdp alternate queries", () => {
    const alts = alternateQueries("rdp hardening");
    expect(alts.some((q) => q.toLowerCase().includes("remote desktop"))).toBe(true);
  });

  it("keeps original query", () => {
    expect(alternateQueries("bitlocker")[0]).toBe("bitlocker");
  });
});
