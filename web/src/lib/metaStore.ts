import { writable } from "svelte/store";
import { fetchMeta, fetchSearchDocuments } from "./api";
import { buildSearchIndex } from "./search";
import type { LoadState, Meta } from "./types";

export const meta = writable<Meta | null>(null);
export const metaState = writable<LoadState>("idle");
export const metaError = writable<string | null>(null);
export const searchState = writable<LoadState>("idle");
export const searchError = writable<string | null>(null);

let bootPromise: Promise<void> | null = null;
let lastBootFailed = false;

export function bootData(force = false): Promise<void> {
  if (bootPromise && !force && !lastBootFailed) return bootPromise;
  lastBootFailed = false;
  bootPromise = (async () => {
    metaState.set("loading");
    searchState.set("loading");
    try {
      const m = await fetchMeta();
      meta.set(m);
      metaState.set("success");
      metaError.set(null);
    } catch (e) {
      metaState.set("error");
      metaError.set(e instanceof Error ? e.message : String(e));
    }
    try {
      const docs = await fetchSearchDocuments();
      if (!docs.length) {
        throw new Error("Search index loaded 0 documents");
      }
      await buildSearchIndex(docs);
      searchState.set("success");
      searchError.set(null);
    } catch (e) {
      lastBootFailed = true;
      searchState.set("error");
      searchError.set(e instanceof Error ? e.message : String(e));
    }
  })();
  return bootPromise;
}
