/**
 * Search API — MiniSearch runs in a Web Worker when available (B-040).
 * Falls back to main-thread engine (tests / no Worker / worker timeout).
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
  {
    resolve: (v: unknown) => void;
    reject: (e: Error) => void;
    timer?: ReturnType<typeof setTimeout>;
  }
>();

const WORKER_BUILD_TIMEOUT_MS = 20_000;
const WORKER_SEARCH_TIMEOUT_MS = 8_000;

function canUseWorker(): boolean {
  return typeof Worker !== "undefined";
}

function rejectAllPending(err: Error): void {
  for (const [, p] of pending) {
    if (p.timer) clearTimeout(p.timer);
    p.reject(err);
  }
  pending.clear();
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
      if (p.timer) clearTimeout(p.timer);
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
      useWorker = false;
      rejectAllPending(new Error("Search worker failed"));
      try {
        worker?.terminate();
      } catch {
        /* ignore */
      }
      worker = null;
    };
    useWorker = true;
    return worker;
  } catch (e) {
    console.warn("search worker unavailable, using main thread", e);
    useWorker = false;
    return null;
  }
}

function postWorker<T>(
  msg: Omit<WorkerIn, "requestId"> & { requestId?: number },
  timeoutMs: number,
): Promise<T> {
  const w = ensureWorker();
  if (!w) return Promise.reject(new Error("no worker"));
  const requestId = ++reqSeq;
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(requestId);
      reject(new Error(`Search worker timeout after ${timeoutMs}ms`));
    }, timeoutMs);
    pending.set(requestId, {
      resolve: resolve as (v: unknown) => void,
      reject,
      timer,
    });
    w.postMessage({ ...msg, requestId } as WorkerIn);
  });
}

function buildMainThread(docs: SearchDoc[]): void {
  engine = createEngine(docs);
  ready = true;
  useWorker = false;
}

export function isSearchReady(): boolean {
  return ready;
}

export function getAllDocs(): SearchDoc[] {
  return allDocs;
}

/** Build index (async when worker is used). Always keeps main-thread fallback path. */
export async function buildSearchIndex(docs: SearchDoc[]): Promise<void> {
  allDocs = docs;
  docsById = new Map(docs.map((d) => [d.id, d]));
  ready = false;
  engine = null;

  if (!docs.length) {
    ready = true;
    return;
  }

  const w = ensureWorker();
  if (w && useWorker) {
    try {
      await postWorker<number>(
        { type: "build", docs },
        WORKER_BUILD_TIMEOUT_MS,
      );
      // Also keep a main-thread engine so sync helpers / CCI work offline of worker
      try {
        engine = createEngine(docs);
      } catch (e) {
        console.warn("main-thread index clone failed (worker still active)", e);
      }
      ready = true;
      return;
    } catch (e) {
      console.warn("search worker build failed — main-thread fallback", e);
      useWorker = false;
      try {
        worker?.terminate();
      } catch {
        /* ignore */
      }
      worker = null;
    }
  }

  buildMainThread(docs);
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
  if (!ready) return [];

  const { alternateQueries } = await import("./synonyms");
  const queries = alternateQueries(query);

  const mergeOne = async (q: string): Promise<SearchDoc[]> => {
    if (useWorker && worker) {
      try {
        return await postWorker<SearchDoc[]>(
          {
            type: "search",
            query: q,
            limit,
            filters,
          },
          WORKER_SEARCH_TIMEOUT_MS,
        );
      } catch (e) {
        console.warn("worker search failed, main-thread fallback", e);
        useWorker = false;
      }
    }
    return searchWithEngine(engine, allDocs, docsById, q, limit, filters);
  };

  if (queries.length <= 1) {
    return mergeOne(query);
  }
  const seen = new Set<string>();
  const out: SearchDoc[] = [];
  for (const q of queries) {
    const batch = await mergeOne(q);
    for (const d of batch) {
      if (seen.has(d.id)) continue;
      seen.add(d.id);
      out.push(d);
      if (out.length >= limit) return out;
    }
  }
  return out;
}

/** Sync search (main-thread engine — used by tests). */
export function search(
  query: string,
  limit = 40,
  filters?: SearchFilters,
): SearchDoc[] {
  if (!engine) {
    // Worker-only without main clone: empty for sync API
    if (useWorker) return [];
    return [];
  }
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
      return await postWorker<string[]>(
        { type: "vendors" },
        WORKER_SEARCH_TIMEOUT_MS,
      );
    } catch {
      /* fall through */
    }
  }
  return uniqueVendors(allDocs);
}
