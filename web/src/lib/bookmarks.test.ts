import { describe, it, expect, beforeEach } from "vitest";
import { bookmarks, isBookmarked, toggleBookmark } from "./bookmarks";
import { get } from "svelte/store";

const KEY = "stigref-bookmarks-v1";

beforeEach(() => {
  localStorage.clear();
  bookmarks.set([]);
});

describe("bookmarks", () => {
  it("toggles a rule bookmark on and off", () => {
    expect(isBookmarked("rule", "SV-1")).toBe(false);
    toggleBookmark({ type: "rule", id: "SV-1", title: "Rule one" });
    expect(isBookmarked("rule", "SV-1")).toBe(true);
    expect(get(bookmarks)).toHaveLength(1);
    toggleBookmark({ type: "rule", id: "SV-1", title: "Rule one" });
    expect(isBookmarked("rule", "SV-1")).toBe(false);
    expect(get(bookmarks)).toHaveLength(0);
  });

  it("persists to localStorage", () => {
    toggleBookmark({ type: "stig", id: "s1", title: "STIG" });
    const raw = localStorage.getItem(KEY);
    expect(raw).toBeTruthy();
    const parsed = JSON.parse(raw!);
    expect(parsed[0].id).toBe("s1");
    expect(parsed[0].type).toBe("stig");
    expect(parsed[0].savedAt).toBeTruthy();
  });

  it("does not duplicate; toggle removes", () => {
    toggleBookmark({ type: "rule", id: "a", title: "A" });
    toggleBookmark({ type: "rule", id: "a", title: "A again" });
    expect(get(bookmarks)).toHaveLength(0);
  });
});
