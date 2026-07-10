import type { SearchFilters } from "./types";
import { emptyFilters } from "./search";
import { baseUrl } from "./paths";

export function parseSearchParams(search: string = location.search): {
  q: string;
  filters: SearchFilters;
} {
  const sp = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const f = emptyFilters();
  const type = sp.get("type") || "";
  if (type === "stig" || type === "rule" || type === "srg") f.type = type;
  f.severity = sp.get("severity") || "";
  f.vendor = sp.get("vendor") || "";
  f.hasIntune = sp.get("intune") === "1" || sp.get("intune") === "true";
  f.hasCve = sp.get("cve") === "1" || sp.get("cve") === "true";
  f.inKev = sp.get("kev") === "1" || sp.get("kev") === "true";
  f.hasAttack = sp.get("attack") === "1" || sp.get("attack") === "true";
  f.hasCis = sp.get("cis") === "1" || sp.get("cis") === "true";
  f.hasOval = sp.get("oval") === "1" || sp.get("oval") === "true";
  f.hasScap = sp.get("scap") === "1" || sp.get("scap") === "true";
  return { q: sp.get("q") || "", filters: f };
}

export function buildSearchUrl(q: string, filters: SearchFilters): string {
  const sp = new URLSearchParams();
  if (q.trim()) sp.set("q", q.trim());
  if (filters.type) sp.set("type", filters.type);
  if (filters.severity) sp.set("severity", filters.severity);
  if (filters.vendor) sp.set("vendor", filters.vendor);
  if (filters.hasIntune) sp.set("intune", "1");
  if (filters.hasCve) sp.set("cve", "1");
  if (filters.inKev) sp.set("kev", "1");
  if (filters.hasAttack) sp.set("attack", "1");
  if (filters.hasCis) sp.set("cis", "1");
  if (filters.hasOval) sp.set("oval", "1");
  if (filters.hasScap) sp.set("scap", "1");
  const qs = sp.toString();
  const base = baseUrl().replace(/\/$/, "") || "";
  return qs ? `${base}/?${qs}` : `${base}/`;
}

export function replaceSearchUrl(q: string, filters: SearchFilters): void {
  const url = buildSearchUrl(q, filters);
  history.replaceState({}, "", url);
}
