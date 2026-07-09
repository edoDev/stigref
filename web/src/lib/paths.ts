/** Absolute site paths including Vite base (e.g. /stigref/). */

export function baseUrl(): string {
  const b = import.meta.env.BASE_URL || "/";
  return b.endsWith("/") ? b : `${b}/`;
}

/** Join base + path segments into a browser path. */
export function href(...parts: string[]): string {
  const base = baseUrl().replace(/\/$/, "");
  const rest = parts
    .map((p) => p.replace(/^\/+|\/+$/g, ""))
    .filter(Boolean)
    .join("/");
  return rest ? `${base}/${rest}` : `${base}/` || "/";
}

/** URL to a static data file. */
export function dataUrl(...parts: string[]): string {
  return href("data", ...parts);
}

/** App routes (absolute with base). */
export const routes = {
  home: () => href(""),
  about: () => href("about"),
  stigs: () => href("stigs"),
  stig: (id: string) => href("stigs", encodeURIComponent(id)),
  rule: (id: string) => href("rules", encodeURIComponent(id)),
};
