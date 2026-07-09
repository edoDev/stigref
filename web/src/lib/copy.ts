import type { RuleDetail, StigDetail } from "./types";
import { routes } from "./paths";

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch {
      return false;
    }
  }
}

export function ruleCitation(rule: RuleDetail, origin = location.origin): string {
  const stigLine =
    rule.stigs?.length > 0
      ? rule.stigs
          .map((s) => `${s.name} · V${s.version}R${s.release}`)
          .join("; ")
      : "(no STIG link)";
  const link = `${origin}${routes.rule(rule.full_rule_id)}`;
  return [
    `Rule: ${rule.full_rule_id}`,
    `Title: ${rule.title}`,
    `Severity: ${rule.severity || "n/a"}`,
    `STIG: ${stigLine}`,
    `Link: ${link}`,
  ].join("\n");
}

export function stigCitation(stig: StigDetail, origin = location.origin): string {
  const link = `${origin}${routes.stig(stig.id)}`;
  return [
    `STIG: ${stig.name}`,
    `Version: V${stig.version}R${stig.release}`,
    `Release date: ${stig.release_date || "n/a"}`,
    `Rules: ${stig.rule_count}`,
    `Link: ${link}`,
  ].join("\n");
}
