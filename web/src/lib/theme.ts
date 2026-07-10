/** Carbon Green is the only product theme (theme picker removed). */

export type ThemeId = "carbon";

export const themes: Array<{ id: ThemeId; label: string; blurb: string }> = [
  { id: "carbon", label: "Carbon Green", blurb: "Terminal / SOC green" },
];

/** Ensure document uses Carbon; clear any legacy theme localStorage key. */
export function initTheme(): void {
  document.documentElement.dataset.theme = "carbon";
  try {
    localStorage.removeItem("stigref-theme");
  } catch {
    /* ignore */
  }
}
