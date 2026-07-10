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

/** Fetch JSON, preferring precompressed .gz when DecompressionStream is available (B-041). */
async function getJsonPreferGzip<T>(plainUrl: string, gzUrl?: string): Promise<T> {
  const canGunzip =
    typeof DecompressionStream !== "undefined" && typeof Response !== "undefined";
  if (canGunzip && gzUrl) {
    try {
      const res = await fetch(gzUrl);
      if (res.ok) {
        const ds = new DecompressionStream("gzip");
        const stream = res.body?.pipeThrough(ds);
        if (stream) {
          const text = await new Response(stream).text();
          return JSON.parse(text) as T;
        }
      }
    } catch {
      /* fall through to plain */
    }
  }
  return getJson<T>(plainUrl);
}

export function fetchMeta(): Promise<Meta> {
  return getJson<Meta>(dataUrl("meta.json"));
}

interface SearchManifest {
  version?: number;
  format?: string;
  total?: number;
  preferGzip?: boolean;
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
      const parts = await Promise.all(
        man.shards.map(async (s) => {
          const plain = dataUrl("search", ...s.path.split("/"));
          const gz = s.pathGz
            ? dataUrl("search", ...s.pathGz.split("/"))
            : `${plain}.gz`;
          const body = await getJsonPreferGzip<ShardBody>(plain, gz);
          return body.documents ?? [];
        }),
      );
      return parts.flat();
    }
  } catch {
    /* legacy path */
  }

  // Legacy monolithic documents.json
  try {
    const body = await getJsonPreferGzip<{ documents: SearchDoc[]; total: number }>(
      dataUrl("search", "documents.json"),
      dataUrl("search", "documents.json.gz"),
    );
    return body.documents ?? [];
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
