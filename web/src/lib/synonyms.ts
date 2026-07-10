/** Search synonym expansion — B-032 */

/** User query tokens → alternate search tokens (lowercase). */
export const SYNONYMS: Record<string, string[]> = {
  rdp: ["remote desktop", "terminal services"],
  av: ["antivirus", "defender"],
  firewall: ["defender firewall", "windows firewall"],
  bitlocker: ["device encryption", "fve"],
  uac: ["user account control", "elevation"],
  gpo: ["group policy"],
  intune: ["mdm", "endpoint manager"],
  smb: ["smbv1", "smb1", "cifs"],
  pwd: ["password"],
  pw: ["password"],
  auth: ["authentication", "logon", "login"],
  admin: ["administrator", "privileged"],
  sehop: ["structured exception", "overwrite protection"],
  tls: ["ssl", "schannel"],
  ntlm: ["lm compatibility"],
  lsa: ["lsass", "credential guard"],
  audit: ["event log", "logging"],
  pin: ["passcode", "device password"],
  wifi: ["wlan", "wireless"],
  bluetooth: ["bt"],
  chrome: ["google chrome"],
  edge: ["microsoft edge"],
};

/** Expand query with synonyms (appends alternates; keeps original). */
export function expandQuery(q: string): string {
  const raw = q.trim();
  if (!raw) return raw;
  const lower = raw.toLowerCase();
  const extras: string[] = [];
  for (const [key, alts] of Object.entries(SYNONYMS)) {
    if (lower === key || lower.includes(` ${key} `) || lower.startsWith(`${key} `) || lower.endsWith(` ${key}`)) {
      extras.push(...alts);
    }
    // also expand if any alt is present → include key
    for (const a of alts) {
      if (lower.includes(a)) {
        extras.push(key);
        extras.push(...alts.filter((x) => x !== a));
      }
    }
  }
  if (!extras.length) return raw;
  // MiniSearch AND would be too strict with all terms; use OR-friendly space bag
  // by returning original + unique extras (engine still ANDs words — so prefer
  // searching original first; callers may run dual search).
  const uniq = [...new Set(extras.map((e) => e.trim()).filter(Boolean))];
  return `${raw} ${uniq.join(" ")}`.trim();
}

/**
 * For MiniSearch combineWith AND, expansion can hurt. Provide alternate queries
 * to search and merge (B-032).
 */
export function alternateQueries(q: string): string[] {
  const raw = q.trim();
  if (!raw) return [""];
  const out = new Set<string>([raw]);
  const lower = raw.toLowerCase();
  for (const [key, alts] of Object.entries(SYNONYMS)) {
    if (lower.includes(key)) {
      for (const a of alts) {
        out.add(raw.replace(new RegExp(key, "ig"), a));
      }
    }
    for (const a of alts) {
      if (lower.includes(a.toLowerCase())) {
        out.add(raw.replace(new RegExp(a.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "ig"), key));
      }
    }
  }
  return [...out].slice(0, 6);
}
