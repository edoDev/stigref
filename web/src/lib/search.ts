/**
 * Search API — MiniSearch runs in a Web Worker when available (B-040).
 * Falls back to main-thread engine (tests / no Worker).
 */
import type MiniSearch from "minisearch";
import type { SearchDoc, SearchFilters } from "./types";
import {
  applyFilters,
  createEngine,
  emptyFilters,
  searchWithEngine,
  uniqueVendors,
} from "./searchCore";
import type { WorkerIn, WorkerOut } from "./search.worker";

export { applyFilters, emptyFilters };

let engine: MiniSearch<SearchDoc> | null = null;
let allDocs: SearchDoc[] = [];
let docsById = new Map<string, SearchDoc>();
let ready = false;

let worker: Worker | null = null;
let useWorker = false;
let reqSeq = 0;
const pending = new Map<
  number,
  { resolve: (v: unknown) => void; reject: (e: Error) => void }
>();

function canUseWorker(): boolean {
  return typeof Worker !== "undefined";
}

function ensureWorker(): Worker | null {
  if (!canUseWorker()) return null;
  if (worker) return worker;
  try {
    worker = new Worker(new URL("./search.worker.ts", import.meta.url), {
      type: "module",
    });
    worker.onmessage = (ev: MessageEvent<WorkerOut>) => {
      const msg = ev.data;
      const p = pending.get(msg.requestId);
      if (!p) return;
      pending.delete(msg.requestId);
      if (msg.type === "error") {
        p.reject(new Error(msg.message));
        return;
      }
      if (msg.type === "ready") {
        ready = true;
        p.resolve(msg.count);
        return;
      }
      if (msg.type === "results") {
        p.resolve(msg.results);
        return;
      }
      if (msg.type === "vendors") {
        p.resolve(msg.vendors);
      }
    };
    worker.onerror = (err) => {
      console.error("search worker error", err);
    };
    useWorker = true;
    return worker;
  } catch (e) {
    console.warn("search worker unavailable, using main thread", e);
    useWorker = false;
    return null;
  }
}

function postWorker<T>(msg: Omit<WorkerIn, "requestId"> & { requestId?: number }): Promise<T> {
  const w = ensureWorker();
  if (!w) return Promise.reject(new Error("no worker"));
  const requestId = ++reqSeq;
  return new Promise<T>((resolve, reject) => {
    pending.set(requestId, {
      resolve: resolve as (v: unknown) => void,
      reject,
    });
    w.postMessage({ ...msg, requestId } as WorkerIn);
  });
}

export function isSearchReady(): boolean {
  return ready;
}

export function getAllDocs(): SearchDoc[] {
  return allDocs;
}

/** Build index (async when worker is used). */
export async function buildSearchIndex(docs: SearchDoc[]): Promise<void> {
  allDocs = docs;
  docsById = new Map(docs.map((d) => [d.id, d]));
  ready = false;

  const w = ensureWorker();
  if (w && useWorker) {
    await postWorker<number>({ type: "build", docs });
    ready = true;
    return;
  }

  // Main-thread fallback
  engine = createEngine(docs);
  ready = true;
}

/** Synchronous build for unit tests / environments without Worker. */
export function buildSearchIndexSync(docs: SearchDoc[]): void {
  allDocs = docs;
  docsById = new Map(docs.map((d) => [d.id, d]));
  engine = createEngine(docs);
  ready = true;
  useWorker = false;
}

export async function searchAsync(
  query: string,
  limit = 40,
  filters?: SearchFilters,
): Promise<SearchDoc[]> {
  if (!ready && !engine) return [];
  // B-032: synonym alternate queries, merge unique hits
  const { alternateQueries } = await import("./synonyms");
  const queries = alternateQueries(query);
  const merge = async (q: string) => {
    if (useWorker && worker) {
      return postWorker<SearchDoc[]>({
        type: "search",
        query: q,
        limit,
        filters,
      });
    }
    return searchWithEngine(engine, allDocs, docsById, q, limit, filters);
  };
  if (queries.length <= 1) {
    return merge(query);
  }
  const seen = new Set<string>();
  const out: SearchDoc[] = [];
  for (const q of queries) {
    const batch = await merge(q);
    for (const d of batch) {
      if (seen.has(d.id)) continue;
      seen.add(d.id);
      out.push(d);
      if (out.length >= limit) return out;
    }
  }
  return out;
}

/** Sync search (main-thread engine only — used by tests). */
export function search(
  query: string,
  limit = 40,
  filters?: SearchFilters,
): SearchDoc[] {
  if (!engine && useWorker) {
    // Worker-only: return empty; callers should use searchAsync after ready
    return [];
  }
  // Keep tests simple: primary query only (async path does synonym merge)
  return searchWithEngine(engine, allDocs, docsById, query, limit, filters);
}

/** @deprecated use search() */
export function searchPreferRuleId(
  query: string,
  limit = 40,
  filters?: SearchFilters,
): SearchDoc[] {
  return search(query, limit, filters);
}

export function uniqueVendorsFromIndex(): string[] {
  return uniqueVendors(allDocs);
}

export async function uniqueVendorsFromIndexAsync(): Promise<string[]> {
  if (useWorker && worker && ready) {
    try {
      return await postWorker<string[]>({ type: "vendors" });
    } catch {
      /* fall through */
    }
  }
  return uniqueVendors(allDocs);
}
