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
  kev: () => href("kev"),
  saved: () => href("saved"),
  products: () => href("products"),
  product: (id: string) => href("products", encodeURIComponent(id)),
  help: () => href("help"),
  releases: () => href("releases"),
  compare: (a?: string, b?: string) => {
    const base = href("compare");
    if (!a && !b) return base;
    const sp = new URLSearchParams();
    if (a) sp.set("a", a);
    if (b) sp.set("b", b);
    return `${base}?${sp}`;
  },
  cci: () => href("cci"),
  cciId: (id: string) => href("cci", encodeURIComponent(id)),
  vendors: () => href("vendors"),
  vendor: (id: string) => href("vendors", encodeURIComponent(id)),
  tools: () => href("tools"),
  nist: () => href("nist"),
  cis: () => href("cis"),
};
