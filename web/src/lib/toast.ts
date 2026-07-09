import { writable } from "svelte/store";

export const toastMessage = writable<string | null>(null);

let timer: ReturnType<typeof setTimeout> | null = null;

export function toast(msg: string, ms = 1800): void {
  toastMessage.set(msg);
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => toastMessage.set(null), ms);
}
