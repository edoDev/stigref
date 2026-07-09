import { writable } from "svelte/store";

export type Bookmark =
  | { type: "rule"; id: string; title: string; savedAt: string }
  | { type: "stig"; id: string; title: string; savedAt: string }
  | { type: "query"; id: string; title: string; query: string; savedAt: string };

const KEY = "stigref-bookmarks-v1";
const MAX = 100;

function load(): Bookmark[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Bookmark[];
    return Array.isArray(parsed) ? parsed.slice(0, MAX) : [];
  } catch {
    return [];
  }
}

function save(list: Bookmark[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)));
  } catch {
    /* ignore */
  }
}

export const bookmarks = writable<Bookmark[]>(
  typeof localStorage !== "undefined" ? load() : [],
);

bookmarks.subscribe((list) => {
  if (typeof localStorage !== "undefined") save(list);
});

export function isBookmarked(type: Bookmark["type"], id: string): boolean {
  let list: Bookmark[] = [];
  bookmarks.subscribe((b) => (list = b))();
  return list.some((x) => x.type === type && x.id === id);
}

export function toggleBookmark(item: Omit<Bookmark, "savedAt"> & { savedAt?: string }): void {
  bookmarks.update((list) => {
    const idx = list.findIndex((x) => x.type === item.type && x.id === item.id);
    if (idx >= 0) {
      return [...list.slice(0, idx), ...list.slice(idx + 1)];
    }
    const entry = {
      ...item,
      savedAt: new Date().toISOString(),
    } as Bookmark;
    return [entry, ...list].slice(0, MAX);
  });
}
