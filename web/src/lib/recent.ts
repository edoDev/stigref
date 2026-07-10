/** Recently viewed rules/STIGs (local only) — B-030 */

export type RecentItem =
  | { type: "rule"; id: string; title: string; at: string }
  | { type: "stig"; id: string; title: string; at: string };

const KEY = "stigref-recent-v1";
const MAX = 20;

function load(): RecentItem[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as RecentItem[];
    return Array.isArray(parsed) ? parsed.slice(0, MAX) : [];
  } catch {
    return [];
  }
}

function save(list: RecentItem[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)));
  } catch {
    /* ignore */
  }
}

export function getRecent(): RecentItem[] {
  if (typeof localStorage === "undefined") return [];
  return load();
}

export function pushRecent(item: Omit<RecentItem, "at">): void {
  if (typeof localStorage === "undefined") return;
  const list = load().filter((x) => !(x.type === item.type && x.id === item.id));
  list.unshift({ ...item, at: new Date().toISOString() } as RecentItem);
  save(list);
}

export function clearRecent(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
