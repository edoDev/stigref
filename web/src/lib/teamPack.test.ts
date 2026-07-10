import { describe, it, expect } from "vitest";
import { buildTeamPack, checklistToCsv, parseTeamPack } from "./teamPack";

describe("teamPack", () => {
  it("round-trips JSON", () => {
    const pack = buildTeamPack("t", [{ id: "SV-1", title: "One" }]);
    const parsed = parseTeamPack(JSON.stringify(pack));
    expect(parsed.rules).toHaveLength(1);
    expect(parsed.format).toBe("stigref-team-pack/v1");
  });

  it("exports csv", () => {
    const csv = checklistToCsv([{ id: "SV-1", title: "A", status: "todo", note: "x" }]);
    expect(csv).toContain("ruleId,title");
    expect(csv).toContain("SV-1");
  });
});
