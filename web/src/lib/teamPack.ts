/** Team pack JSON import/export (B-052) */

export interface TeamPack {
  format: "stigref-team-pack/v1";
  name: string;
  createdAt: string;
  rules: Array<{ id: string; title?: string; note?: string }>;
}

export function buildTeamPack(
  name: string,
  rules: Array<{ id: string; title?: string; note?: string }>,
): TeamPack {
  return {
    format: "stigref-team-pack/v1",
    name: name || "stigref pack",
    createdAt: new Date().toISOString(),
    rules,
  };
}

export function parseTeamPack(raw: string): TeamPack {
  const data = JSON.parse(raw) as TeamPack;
  if (!data || data.format !== "stigref-team-pack/v1" || !Array.isArray(data.rules)) {
    throw new Error("Invalid team pack (expected format stigref-team-pack/v1)");
  }
  return data;
}

export function checklistToCsv(
  rows: Array<{ id: string; title?: string; status?: string; note?: string }>,
): string {
  const esc = (v: string) => {
    const t = v ?? "";
    if (/[",\n]/.test(t)) return `"${t.replace(/"/g, '""')}"`;
    return t;
  };
  const lines = ["ruleId,title,status,note"];
  for (const r of rows) {
    lines.push(
      [esc(r.id), esc(r.title || ""), esc(r.status || ""), esc(r.note || "")].join(","),
    );
  }
  return lines.join("\n") + "\n";
}
