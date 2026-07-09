import { writable } from "svelte/store";

export type ThemeId = "slate" | "carbon" | "violet" | "amber";

export const themes: Array<{ id: ThemeId; label: string; blurb: string }> = [
  { id: "slate", label: "Midnight Slate", blurb: "Cool blue-gray (default)" },
  { id: "carbon", label: "Carbon Green", blurb: "Terminal / SOC green" },
  { id: "violet", label: "Violet Dusk", blurb: "Soft purple accents" },
  { id: "amber", label: "Amber Forge", blurb: "Warm amber on charcoal" },
];

const KEY = "stigref-theme";

function read(): ThemeId {
  try {
    const v = localStorage.getItem(KEY) as ThemeId | null;
    if (v && themes.some((t) => t.id === v)) return v;
  } catch {
    /* ignore */
  }
  return "slate";
}

export const theme = writable<ThemeId>(typeof localStorage !== "undefined" ? read() : "slate");

export function applyTheme(id: ThemeId): void {
  document.documentElement.dataset.theme = id;
  try {
    localStorage.setItem(KEY, id);
  } catch {
    /* ignore */
  }
  theme.set(id);
}

export function initTheme(): void {
  applyTheme(read());
}
