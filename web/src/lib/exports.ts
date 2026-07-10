/** Rule / CIS export helpers — CSV & Markdown */

import type { RuleDetail } from "./types";
import { routes } from "./paths";

function escCsv(v: string): string {
  const t = v ?? "";
  if (/[",\n\r]/.test(t)) return `"${t.replace(/"/g, '""')}"`;
  return t;
}

/** Full rule export as Markdown (includes CIS side-by-side). */
export function ruleExportMarkdown(
  rule: RuleDetail,
  origin = typeof location !== "undefined" ? location.origin : "",
): string {
  const link = `${origin}${routes.rule(rule.full_rule_id)}`;
  const lines: string[] = [
    `# ${rule.full_rule_id}`,
    "",
    `**${rule.title}**`,
    "",
    `| Field | Value |`,
    `| --- | --- |`,
    `| Severity | ${rule.severity || "n/a"} |`,
    `| Group | ${rule.group_id || "—"} |`,
    `| CCI | ${(rule.ccis || []).join(", ") || "—"} |`,
    `| CVE | ${(rule.cves || []).join(", ") || "—"} |`,
    "",
    `[Open in stigref](${link})`,
    "",
    "## STIG Check",
    "",
    "```",
    rule.check || "—",
    "```",
    "",
    "## STIG Fix",
    "",
    "```",
    rule.fix || "—",
    "```",
    "",
  ];

  const cis = rule.cis?.items || [];
  if (cis.length) {
    lines.push("## CIS Benchmark crosswalk", "");
    lines.push(
      "| CIS ID | Title | Profile | Relationship | Confidence | Notes |",
    );
    lines.push("| --- | --- | --- | --- | --- | --- |");
    for (const c of cis) {
      lines.push(
        `| ${c.id} | ${c.title || ""} | ${c.profile || ""} | ${c.relationship || ""} | ${c.confidence || ""} | ${(c.notes || "").replace(/\|/g, "/")} |`,
      );
    }
    lines.push("");
    if (cis[0]?.benchmark) {
      lines.push(`Benchmark: **${cis[0].benchmark}** (${cis[0].benchmarkVersion || "n/a"})`);
      lines.push("");
    }
    lines.push(
      `> ${rule.cis?.disclaimer || "CIS mapping is assistive; official CIS text is authoritative."}`,
    );
    lines.push("");
  } else {
    lines.push("## CIS Benchmark crosswalk", "", "_No curated CIS mapping for this rule._", "");
  }

  const sugs = rule.intune?.suggestions || [];
  if (sugs.length) {
    lines.push("## Intune / CSP suggestions", "");
    for (const s of sugs) {
      lines.push(`- **${s.title || s.cspId || "setting"}** (${s.confidence || "?"} conf)`);
      if (s.settingsCatalogName) lines.push(`  - Settings Catalog: ${s.settingsCatalogName}`);
      if (s.omaUri) lines.push(`  - OMA-URI: \`${s.omaUri}\``);
      if (s.value != null && s.value !== "") lines.push(`  - Value: \`${s.value}\``);
    }
    lines.push("");
  }

  return lines.join("\n");
}

/** Rule + CIS rows as CSV (one row per CIS item, or one row if none). */
export function ruleExportCsv(rule: RuleDetail): string {
  const header = [
    "full_rule_id",
    "title",
    "severity",
    "group_id",
    "ccis",
    "cves",
    "cis_id",
    "cis_title",
    "cis_profile",
    "cis_relationship",
    "cis_confidence",
    "cis_benchmark",
    "cis_notes",
  ];
  const base = [
    rule.full_rule_id,
    rule.title || "",
    rule.severity || "",
    rule.group_id || "",
    (rule.ccis || []).join(";"),
    (rule.cves || []).join(";"),
  ];
  const items = rule.cis?.items || [];
  const rows: string[] = [header.join(",")];
  if (!items.length) {
    rows.push(
      [...base, "", "", "", "", "", "", ""].map((c) => escCsv(String(c))).join(","),
    );
  } else {
    for (const c of items) {
      rows.push(
        [
          ...base,
          c.id || "",
          c.title || "",
          c.profile || "",
          c.relationship || "",
          c.confidence || "",
          c.benchmark || "",
          c.notes || "",
        ]
          .map((x) => escCsv(String(x)))
          .join(","),
      );
    }
  }
  return rows.join("\n") + "\n";
}

/** STIG check vs CIS notes side-by-side Markdown table. */
export function ruleStigCisCompareMarkdown(rule: RuleDetail): string {
  const cis = rule.cis?.items || [];
  const lines = [
    `# STIG ↔ CIS: ${rule.full_rule_id}`,
    "",
    `**${rule.title}**`,
    "",
    "## Side-by-side",
    "",
    "| STIG | CIS |",
    "| --- | --- |",
    `| **ID** ${rule.full_rule_id} | **IDs** ${cis.map((c) => c.id).join(", ") || "—"} |`,
    `| **Severity** ${rule.severity || "n/a"} | **Profiles** ${[...new Set(cis.map((c) => c.profile).filter(Boolean))].join(", ") || "—"} |`,
    "",
    "### STIG Check",
    "",
    "```",
    rule.check || "—",
    "```",
    "",
    "### CIS linked recommendations",
    "",
  ];
  if (!cis.length) {
    lines.push("_No CIS mapping._");
  } else {
    for (const c of cis) {
      lines.push(
        `#### ${c.id} — ${c.title || "(title)"}`,
        "",
        `- Relationship: **${c.relationship || "related"}** (${c.confidence || "?"} confidence)`,
        `- Benchmark: ${c.benchmark || "—"} ${c.benchmarkVersion || ""}`,
        `- Profile: ${c.profile || "—"}`,
        `- Notes: ${c.notes || "—"}`,
        "",
      );
    }
  }
  lines.push(
    "### STIG Fix",
    "",
    "```",
    rule.fix || "—",
    "```",
    "",
    `> ${rule.cis?.disclaimer || "CIS mapping assistive only."}`,
    "",
  );
  return lines.join("\n");
}

export function downloadText(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
