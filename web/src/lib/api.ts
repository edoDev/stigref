import { dataUrl } from "./paths";
import type {
  Meta,
  RuleDetail,
  SearchDoc,
  StigDetail,
  StigIndexEntry,
  TagsCatalog,
} from "./types";

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText} for ${url}`);
  }
  return res.json() as Promise<T>;
}

function isGzipMagic(buf: ArrayBuffer): boolean {
  if (buf.byteLength < 2) return false;
  const u8 = new Uint8Array(buf);
  return u8[0] === 0x1f && u8[1] === 0x8b;
}

/** Decompress a gzip ArrayBuffer to text (DecompressionStream). */
async function gunzipToText(buf: ArrayBuffer): Promise<string> {
  if (typeof DecompressionStream === "undefined") {
    throw new Error("DecompressionStream not available");
  }
  const ds = new DecompressionStream("gzip");
  const stream = new Response(buf).body?.pipeThrough(ds);
  if (!stream) throw new Error("No body stream for gunzip");
  return new Response(stream).text();
}

/**
 * Fetch JSON, preferring precompressed .gz when available (B-041).
 * Robust against:
 * - gzipOnly shards (plain 404)
 * - browsers without DecompressionStream (plain path)
 * - accidental double-encoding / already-decompressed responses
 */
async function getJsonPreferGzip<T>(plainUrl: string, gzUrl?: string): Promise<T> {
  const canGunzip = typeof DecompressionStream !== "undefined";

  if (canGunzip && gzUrl) {
    try {
      const res = await fetch(gzUrl);
      if (res.ok) {
        const buf = await res.arrayBuffer();
        if (isGzipMagic(buf)) {
          const text = await gunzipToText(buf);
          return JSON.parse(text) as T;
        }
        // Server may have already decompressed (or served plain JSON with .gz name)
        const text = new TextDecoder("utf-8").decode(buf);
        return JSON.parse(text) as T;
      }
    } catch {
      /* try plain */
    }
  }

  try {
    return await getJson<T>(plainUrl);
  } catch (plainErr) {
    // Last resort: gz without DecompressionStream is not usable
    if (gzUrl && !canGunzip) {
      throw new Error(
        `Cannot load ${gzUrl}: browser lacks DecompressionStream and plain fallback failed (${plainErr instanceof Error ? plainErr.message : plainErr})`,
      );
    }
    throw plainErr;
  }
}

export function fetchMeta(): Promise<Meta> {
  return getJson<Meta>(dataUrl("meta.json"));
}

interface SearchManifest {
  version?: number;
  format?: string;
  total?: number;
  preferGzip?: boolean;
  gzipOnly?: boolean;
  shards?: Array<{
    id: string;
    path: string;
    pathGz?: string;
    count?: number;
  }>;
}

interface ShardBody {
  documents?: SearchDoc[];
  count?: number;
}

/** Load search docs from sharded+gzip index, with legacy monolith fallback (B-041). */
export async function fetchSearchDocuments(): Promise<SearchDoc[]> {
  // Prefer shard manifest
  try {
    const man = await getJsonPreferGzip<SearchManifest>(
      dataUrl("search", "manifest.json"),
      dataUrl("search", "manifest.json.gz"),
    );
    if (man.shards?.length) {
      const results = await Promise.all(
        man.shards.map(async (s) => {
          const plain = dataUrl("search", ...s.path.split("/"));
          const gz = s.pathGz
            ? dataUrl("search", ...s.pathGz.split("/"))
            : `${plain}.gz`;
          try {
            const body = await getJsonPreferGzip<ShardBody>(plain, gz);
            return { ok: true as const, docs: body.documents ?? [], id: s.id };
          } catch (e) {
            return {
              ok: false as const,
              id: s.id,
              error: e instanceof Error ? e.message : String(e),
            };
          }
        }),
      );
      const failed = results.filter((r) => !r.ok);
      const docs = results.flatMap((r) => (r.ok ? r.docs : []));
      if (!docs.length) {
        throw new Error(
          `Search shards loaded 0 documents (${failed.length}/${man.shards.length} failed). ${failed[0] && !failed[0].ok ? failed[0].error : ""}`,
        );
      }
      if (failed.length) {
        console.warn(
          `Search: ${failed.length} shard(s) failed; loaded ${docs.length} docs`,
          failed,
        );
      }
      // Sanity: warn if far below manifest total
      if (man.total && docs.length < man.total * 0.5) {
        console.warn(
          `Search: only ${docs.length}/${man.total} documents loaded — index may be incomplete`,
        );
      }
      return docs;
    }
  } catch (e) {
    console.warn("Search shard load failed, trying legacy documents.json", e);
  }

  // Legacy monolithic documents.json
  try {
    const body = await getJsonPreferGzip<{ documents: SearchDoc[]; total: number }>(
      dataUrl("search", "documents.json"),
      dataUrl("search", "documents.json.gz"),
    );
    const docs = body.documents ?? [];
    if (!docs.length) {
      throw new Error("Search index is empty (documents.json)");
    }
    return docs;
  } catch (e) {
    throw e instanceof Error ? e : new Error(String(e));
  }
}

export async function fetchStigIndex(): Promise<StigIndexEntry[]> {
  const body = await getJson<{ stigs: StigIndexEntry[]; total: number }>(
    dataUrl("stigs", "index.json"),
  );
  return body.stigs ?? [];
}

export function fetchStig(id: string): Promise<StigDetail> {
  return getJson<StigDetail>(dataUrl("stigs", "by-id", `${id}.json`));
}

export function fetchRule(id: string): Promise<RuleDetail> {
  return getJson<RuleDetail>(dataUrl("rules", "by-id", `${id}.json`));
}

export function fetchTagsCatalog(): Promise<TagsCatalog> {
  return getJson<TagsCatalog>(dataUrl("tags", "catalog.json"));
}

export function intuneProductUrl(productId: string): string {
  return dataUrl("intune", "products", `${productId}.json`);
}

export function fetchIntuneIndex(): Promise<import("./types").IntuneProductIndex> {
  return getJson(dataUrl("intune", "index.json"));
}
