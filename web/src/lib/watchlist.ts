/** Local watchlist of rule IDs (B-025) — “changed since release” needs multi-release later */

export interface WatchItem {
  id: string;
  title: string;
  addedAt: string;
}

const KEY = "stigref-watchlist-v1";
const MAX = 200;

function load(): WatchItem[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const p = JSON.parse(raw) as WatchItem[];
    return Array.isArray(p) ? p.slice(0, MAX) : [];
  } catch {
    return [];
  }
}

function save(list: WatchItem[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)));
  } catch {
    /* ignore */
  }
}

export function getWatchlist(): WatchItem[] {
  return typeof localStorage !== "undefined" ? load() : [];
}

export function isWatched(id: string): boolean {
  return getWatchlist().some((w) => w.id === id);
}

export function toggleWatch(id: string, title: string): boolean {
  const list = load();
  const idx = list.findIndex((w) => w.id === id);
  if (idx >= 0) {
    list.splice(idx, 1);
    save(list);
    return false;
  }
  list.unshift({ id, title, addedAt: new Date().toISOString() });
  save(list);
  return true;
}

export function clearWatchlist(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
