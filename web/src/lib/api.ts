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

export function fetchMeta(): Promise<Meta> {
  return getJson<Meta>(dataUrl("meta.json"));
}

export async function fetchSearchDocuments(): Promise<SearchDoc[]> {
  const body = await getJson<{ documents: SearchDoc[]; total: number }>(
    dataUrl("search", "documents.json"),
  );
  return body.documents ?? [];
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
