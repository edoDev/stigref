import { describe, it, expect } from "vitest";
import { parsePath } from "./router";

describe("parsePath", () => {
  it("parses home", () => {
    expect(parsePath("/stigref/")).toEqual({ name: "home" });
    expect(parsePath("/stigref")).toEqual({ name: "home" });
  });

  it("parses static routes", () => {
    expect(parsePath("/stigref/about")).toEqual({ name: "about" });
    expect(parsePath("/stigref/stigs")).toEqual({ name: "stigs" });
    expect(parsePath("/stigref/kev")).toEqual({ name: "kev" });
    expect(parsePath("/stigref/saved")).toEqual({ name: "saved" });
    expect(parsePath("/stigref/products")).toEqual({ name: "products" });
    expect(parsePath("/stigref/help")).toEqual({ name: "help" });
    expect(parsePath("/stigref/releases")).toEqual({ name: "releases" });
  });

  it("parses detail routes with decode", () => {
    expect(parsePath("/stigref/stigs/win11-v1r1")).toEqual({
      name: "stig",
      id: "win11-v1r1",
    });
    expect(parsePath("/stigref/rules/SV-1r1_rule")).toEqual({
      name: "rule",
      id: "SV-1r1_rule",
    });
    expect(parsePath("/stigref/products/windows-11")).toEqual({
      name: "product",
      id: "windows-11",
    });
  });

  it("returns notfound for unknown paths", () => {
    const r = parsePath("/stigref/nope");
    expect(r.name).toBe("notfound");
    if (r.name === "notfound") expect(r.path).toBe("/nope");
  });
});
