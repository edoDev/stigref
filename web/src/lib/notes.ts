/** Personal scratch notes per rule/stig — local only (B-037) */

export type NoteTarget = { type: "rule" | "stig"; id: string };

export interface NoteEntry {
  type: "rule" | "stig";
  id: string;
  text: string;
  status?: "" | "todo" | "review" | "done" | "na";
  updatedAt: string;
}

const KEY = "stigref-notes-v1";

function loadAll(): NoteEntry[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const p = JSON.parse(raw) as NoteEntry[];
    return Array.isArray(p) ? p : [];
  } catch {
    return [];
  }
}

function saveAll(list: NoteEntry[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    /* ignore */
  }
}

export function getNote(type: NoteEntry["type"], id: string): NoteEntry | null {
  return loadAll().find((n) => n.type === type && n.id === id) || null;
}

export function setNote(
  type: NoteEntry["type"],
  id: string,
  text: string,
  status: NoteEntry["status"] = "",
): void {
  const list = loadAll().filter((n) => !(n.type === type && n.id === id));
  if (text.trim() || status) {
    list.unshift({
      type,
      id,
      text,
      status: status || "",
      updatedAt: new Date().toISOString(),
    });
  }
  saveAll(list.slice(0, 500));
}

export function listNotes(): NoteEntry[] {
  return loadAll();
}
