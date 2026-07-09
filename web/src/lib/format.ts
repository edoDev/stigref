export function formatDate(iso: string | undefined | null): string {
  if (!iso) return "unknown";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function severityClass(sev: string | undefined): string {
  const s = (sev || "").toLowerCase();
  if (s === "high" || s === "medium" || s === "low") return s;
  return "";
}
