/** Board-pack export helpers for Library Observatory (B-090). */

import type { InsightsDoc } from "./types";

function escCsv(v: string): string {
  const t = v ?? "";
  if (/[",\n\r]/.test(t)) return `"${t.replace(/"/g, '""')}"`;
  return t;
}

/** One-page Markdown brief for leadership / program staff. */
export function insightsBoardMarkdown(doc: InsightsDoc, origin = ""): string {
  const k = doc.kpis;
  const lines: string[] = [
    `# stigref Library Observatory`,
    "",
    `**Release:** ${doc.releaseId || "—"} · Generated ${doc.generatedAt || "—"}`,
    "",
    "> " + (doc.disclaimers?.general || ""),
    "",
    "## KPI strip",
    "",
    `| Metric | Value |`,
    `| --- | ---: |`,
    `| STIGs | ${k.stigs ?? "—"} |`,
    `| Rules | ${k.rules ?? "—"} |`,
    `| Vendors | ${k.vendors ?? "—"} |`,
    `| Families | ${k.families ?? "—"} |`,
    `| STIGs with GPO package | ${k.stigsWithGpo ?? "—"} |`,
    `| STIGs with Intune package | ${k.stigsWithIntunePackage ?? "—"} |`,
    `| Rules with Intune map | ${k.rulesWithIntuneMap ?? "—"} |`,
    `| Rules with CIS map | ${k.rulesWithCis ?? "—"} |`,
    `| Unique CCIs | ${k.uniqueCcis ?? "—"} |`,
    `| KEV catalog entries | ${doc.kev?.catalogCount ?? "—"} |`,
    `| Search index (gzip) | ${k.searchTransferMBGz ?? "—"} MB |`,
    "",
    "## Severity mix",
    "",
    `| High | Medium | Low | Unknown |`,
    `| ---: | ---: | ---: | ---: |`,
    `| ${doc.severity?.high ?? 0} | ${doc.severity?.medium ?? 0} | ${doc.severity?.low ?? 0} | ${doc.severity?.unknown ?? 0} |`,
    "",
    "## Intune product coverage",
    "",
    `| Product | Rules | Mapped | Coverage | CAT I mapped |`,
    `| --- | ---: | ---: | ---: | ---: |`,
  ];

  for (const p of doc.intuneProducts || []) {
    const catI = p.severityCoverage?.high;
    lines.push(
      `| ${p.product} | ${p.rules} | ${p.mappedRules} | ${p.coveragePct}% | ${catI?.mapped ?? 0}/${catI?.total ?? 0} |`,
    );
  }

  lines.push(
    "",
    "## Automation (STIG-level packages)",
    "",
    `| Both GPO+Intune | GPO only | Intune only | Neither | SHB-related |`,
    `| ---: | ---: | ---: | ---: | ---: |`,
    `| ${doc.automation?.stigs?.both ?? 0} | ${doc.automation?.stigs?.gpoPackage ?? 0} | ${doc.automation?.stigs?.intunePackage ?? 0} | ${doc.automation?.stigs?.neither ?? 0} | ${doc.automation?.stigs?.shb ?? 0} |`,
    "",
    "## Top unmapped CAT I (by product)",
    "",
  );

  for (const p of doc.intuneProducts || []) {
    const gaps = p.unmappedCatI || [];
    if (!gaps.length) continue;
    lines.push(`### ${p.product}`, "");
    for (const g of gaps.slice(0, 8)) {
      lines.push(`- \`${g.id}\` — ${g.title}`);
    }
    lines.push("");
  }

  lines.push(
    "---",
    "",
    `Open live Observatory: ${origin.includes("/insights") ? origin : `${origin.replace(/\/$/, "")}/insights`}`,
    "",
    doc.disclaimers?.intune ? `*Intune: ${doc.disclaimers.intune}*` : "",
    doc.disclaimers?.kev ? `*KEV: ${doc.disclaimers.kev}*` : "",
    "",
  );
  return lines.filter((l) => l !== undefined).join("\n");
}

/** CSV of Intune product scorecards. */
export function insightsIntuneCsv(doc: InsightsDoc): string {
  const header = [
    "product",
    "stigName",
    "rules",
    "mappedRules",
    "coveragePct",
    "settings",
    "catI_total",
    "catI_mapped",
    "catI_pct",
    "conf_high",
    "conf_medium",
    "conf_low",
  ];
  const rows = [header.join(",")];
  for (const p of doc.intuneProducts || []) {
    const h = p.severityCoverage?.high;
    rows.push(
      [
        escCsv(p.product),
        escCsv(p.stigName || ""),
        String(p.rules ?? ""),
        String(p.mappedRules ?? ""),
        String(p.coveragePct ?? ""),
        String(p.settings ?? ""),
        String(h?.total ?? ""),
        String(h?.mapped ?? ""),
        String(h?.pct ?? ""),
        String(p.confidence?.high ?? ""),
        String(p.confidence?.medium ?? ""),
        String(p.confidence?.low ?? ""),
      ].join(","),
    );
  }
  return rows.join("\n") + "\n";
}

/** CSV of top family scorecards. */
export function insightsScorecardsCsv(doc: InsightsDoc): string {
  const header = [
    "vendor",
    "family",
    "name",
    "ruleCount",
    "high",
    "medium",
    "low",
    "hasGpo",
    "hasIntunePackage",
    "shb",
    "intuneCoveragePct",
    "rulesWithCis",
    "rulesWithScap",
  ];
  const rows = [header.join(",")];
  for (const s of doc.scorecards || []) {
    rows.push(
      [
        escCsv(s.vendor || ""),
        escCsv(s.family || ""),
        escCsv(s.name || ""),
        String(s.ruleCount ?? ""),
        String(s.severity?.high ?? ""),
        String(s.severity?.medium ?? ""),
        String(s.severity?.low ?? ""),
        s.hasGpoPackage ? "1" : "0",
        s.hasIntunePackage ? "1" : "0",
        s.shbRelated ? "1" : "0",
        s.intuneCoveragePct == null ? "" : String(s.intuneCoveragePct),
        String(s.rulesWithCis ?? ""),
        String(s.rulesWithScap ?? ""),
      ].join(","),
    );
  }
  return rows.join("\n") + "\n";
}
