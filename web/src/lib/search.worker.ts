/// <reference lib="webworker" />
import type { SearchDoc, SearchFilters } from "./types";
import {
  createEngine,
  emptyFilters,
  searchWithEngine,
  uniqueVendors,
} from "./searchCore";
import type MiniSearch from "minisearch";

let engine: MiniSearch<SearchDoc> | null = null;
let allDocs: SearchDoc[] = [];
let docsById = new Map<string, SearchDoc>();

export type WorkerIn =
  | { type: "build"; docs: SearchDoc[]; requestId: number }
  | {
      type: "search";
      query: string;
      limit: number;
      filters?: SearchFilters;
      requestId: number;
    }
  | { type: "vendors"; requestId: number };

export type WorkerOut =
  | { type: "ready"; requestId: number; count: number }
  | { type: "results"; requestId: number; results: SearchDoc[] }
  | { type: "vendors"; requestId: number; vendors: string[] }
  | { type: "error"; requestId: number; message: string };

const ctx: DedicatedWorkerGlobalScope = self as unknown as DedicatedWorkerGlobalScope;

ctx.onmessage = (ev: MessageEvent<WorkerIn>) => {
  const msg = ev.data;
  try {
    if (msg.type === "build") {
      allDocs = msg.docs;
      docsById = new Map(msg.docs.map((d) => [d.id, d]));
      engine = createEngine(msg.docs);
      const out: WorkerOut = {
        type: "ready",
        requestId: msg.requestId,
        count: msg.docs.length,
      };
      ctx.postMessage(out);
      return;
    }
    if (msg.type === "search") {
      const results = searchWithEngine(
        engine,
        allDocs,
        docsById,
        msg.query,
        msg.limit,
        msg.filters || emptyFilters(),
      );
      const out: WorkerOut = {
        type: "results",
        requestId: msg.requestId,
        results,
      };
      ctx.postMessage(out);
      return;
    }
    if (msg.type === "vendors") {
      const out: WorkerOut = {
        type: "vendors",
        requestId: msg.requestId,
        vendors: uniqueVendors(allDocs),
      };
      ctx.postMessage(out);
    }
  } catch (e) {
    const out: WorkerOut = {
      type: "error",
      requestId: msg.requestId,
      message: e instanceof Error ? e.message : String(e),
    };
    ctx.postMessage(out);
  }
};
