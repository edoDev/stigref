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

export function ruleMarkdown(rule: RuleDetail, origin = location.origin): string {
  const link = `${origin}${routes.rule(rule.full_rule_id)}`;
  const cves = (rule.cves || []).join(", ") || "—";
  return [
    `### ${rule.full_rule_id}`,
    "",
    `**${rule.title}**`,
    "",
    `| Field | Value |`,
    `| --- | --- |`,
    `| Severity | ${rule.severity || "n/a"} |`,
    `| CCI | ${(rule.ccis || []).join(", ") || "—"} |`,
    `| CVE | ${cves} |`,
    "",
    `[Open in stigref](${link})`,
    "",
    "#### Check",
    "",
    "```",
    rule.check || "—",
    "```",
    "",
    "#### Fix",
    "",
    "```",
    rule.fix || "—",
    "```",
  ].join("\n");
}

export function ruleOmaUriPack(rule: RuleDetail): string {
  const rows = (rule.intune?.suggestions || [])
    .filter((s) => s.omaUri)
    .map((s) => {
      const val = s.value != null && s.value !== "" ? String(s.value) : "";
      return `${s.omaUri}\t${val}\t${s.dataType || ""}\t${s.title || ""}`;
    });
  if (!rows.length) return "";
  return ["omaUri\tvalue\tdataType\ttitle", ...rows].join("\n");
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
