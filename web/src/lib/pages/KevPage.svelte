<script lang="ts">
  import { onMount } from "svelte";
  import { dataUrl } from "../paths";
  import { routes } from "../paths";
  import type { LoadState } from "../types";
  import SearchBox from "../components/SearchBox.svelte";
  import ErrorRetry from "../components/ErrorRetry.svelte";

  interface KevEntry {
    cveID: string;
    vendorProject: string;
    product: string;
    vulnerabilityName: string;
    dateAdded: string;
    shortDescription: string;
    requiredAction: string;
    dueDate: string;
    knownRansomwareCampaignUse: string;
    notes: string;
    cwes: string[];
    nvdUrl: string;
    linkedRules: string[];
  }

  interface KevCatalog {
    catalogVersion?: string;
    dateReleased?: string;
    fetchedAt?: string;
    count: number;
    linkedToStigCount?: number;
    linkedRuleCount?: number;
    catalogUrl?: string;
    vulnerabilities: KevEntry[];
    disclaimer?: string;
  }

  const PAGE = 100;

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let catalog = $state<KevCatalog | null>(null);
  let query = $state("");
  let ransomwareOnly = $state(false);
  let linkedOnly = $state(false);
  let vendor = $state("");
  let visible = $state(PAGE);

  async function loadCatalog() {
    state = "loading";
    error = null;
    try {
      const res = await fetch(dataUrl("threat", "kev.json"));
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      catalog = (await res.json()) as KevCatalog;
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(() => {
    const sp = new URLSearchParams(location.search);
    if (sp.get("q")) query = sp.get("q") || "";
    if (sp.get("linked") === "1") linkedOnly = true;
    if (sp.get("ransomware") === "1") ransomwareOnly = true;
    void loadCatalog();
  });

  // Reset pagination when filters change
  $effect(() => {
    void query;
    void ransomwareOnly;
    void linkedOnly;
    void vendor;
    visible = PAGE;
  });

  let vendors = $derived.by(() => {
    if (!catalog) return [] as string[];
    const s = new Set<string>();
    for (const v of catalog.vulnerabilities) {
      if (v.vendorProject) s.add(v.vendorProject);
    }
    return [...s].sort((a, b) => a.localeCompare(b));
  });

  let filtered = $derived.by(() => {
    if (!catalog) return [] as KevEntry[];
    const q = query.trim().toLowerCase();
    return catalog.vulnerabilities.filter((v) => {
      if (ransomwareOnly && (v.knownRansomwareCampaignUse || "").toLowerCase() !== "known")
        return false;
      if (linkedOnly && !(v.linkedRules && v.linkedRules.length)) return false;
      if (vendor && v.vendorProject !== vendor) return false;
      if (!q) return true;
      const blob = [
        v.cveID,
        v.vendorProject,
        v.product,
        v.vulnerabilityName,
        v.shortDescription,
        v.notes,
        ...(v.cwes || []),
      ]
        .join(" ")
        .toLowerCase();
      return blob.includes(q);
    });
  });

  let shown = $derived(filtered.slice(0, visible));
  let linkedCount = $derived(
    catalog?.linkedToStigCount ?? catalog?.linkedRuleCount ?? null,
  );
</script>

<section class="stack">
  <div>
    <h1>CISA KEV catalog</h1>
    <p class="muted">
      Search the Known Exploited Vulnerabilities catalog snapshot shipped with stigref data. Link out
      to NVD and CISA for authoritative detail.
    </p>
  </div>

  {#if state === "loading"}
    <p class="state">Loading KEV catalog…</p>
  {:else if state === "error"}
    <ErrorRetry title="Could not load KEV catalog" message={error} onretry={loadCatalog} />
  {:else if catalog}
    <div class="card muted">
      {catalog.count.toLocaleString()} vulnerabilities
      {#if catalog.dateReleased}
        · catalog released {catalog.dateReleased}
      {/if}
      {#if catalog.catalogVersion}
        · {catalog.catalogVersion}
      {/if}
      {#if linkedCount != null}
        · {linkedCount} linked to STIG rules in this build
      {/if}
      ·
      <a href={catalog.catalogUrl || "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"} target="_blank" rel="noopener"
        >cisa.gov</a
      >
    </div>

    <SearchBox bind:value={query} placeholder="Search CVE, vendor, product, description…" />

    <div class="filters row">
      <label class="field">
        <span class="muted">Vendor</span>
        <select bind:value={vendor}>
          <option value="">All vendors</option>
          {#each vendors as v}
            <option value={v}>{v}</option>
          {/each}
        </select>
      </label>
      <label class="chk">
        <input type="checkbox" bind:checked={ransomwareOnly} />
        Known ransomware use
      </label>
      <label class="chk">
        <input type="checkbox" bind:checked={linkedOnly} />
        Linked to STIG rules
      </label>
      <span class="muted" role="status" aria-live="polite"
        >{shown.length.toLocaleString()} of {filtered.length.toLocaleString()}</span
      >
    </div>

    <h2 class="list-heading">Vulnerabilities</h2>
    <ul class="list card">
      {#each shown as v (v.cveID)}
        <li class="item">
          <div class="row">
            <a class="mono cve" href={v.nvdUrl} target="_blank" rel="noopener">{v.cveID}</a>
            {#if (v.knownRansomwareCampaignUse || "").toLowerCase() === "known"}
              <span class="badge kev">ransomware</span>
            {/if}
            {#if v.linkedRules?.length}
              <span class="badge accent">{v.linkedRules.length} STIG rule(s)</span>
            {/if}
            <span class="muted small">{v.dateAdded}</span>
          </div>
          <div class="title">{v.vulnerabilityName || v.cveID}</div>
          <div class="muted small">
            {v.vendorProject}
            {#if v.product}
              · {v.product}
            {/if}
          </div>
          {#if v.shortDescription}
            <p class="desc">{v.shortDescription}</p>
          {/if}
          {#if v.linkedRules?.length}
            <div class="row links">
              {#each v.linkedRules.slice(0, 5) as rid}
                <a href={routes.rule(rid)}>{rid}</a>
              {/each}
            </div>
          {/if}
          <div class="row" style="margin-top:0.35rem">
            <a class="btn" href={v.nvdUrl} target="_blank" rel="noopener">NVD</a>
            <a
              class="btn"
              href={`https://www.cisa.gov/known-exploited-vulnerabilities-catalog`}
              target="_blank"
              rel="noopener">CISA KEV</a
            >
          </div>
        </li>
      {/each}
    </ul>
    {#if visible < filtered.length}
      <p class="state">
        <button type="button" class="primary" onclick={() => (visible += PAGE)}>
          Show more ({Math.min(PAGE, filtered.length - visible)} of
          {(filtered.length - visible).toLocaleString()} remaining)
        </button>
      </p>
    {/if}
    {#if catalog.disclaimer}
      <p class="muted small">{catalog.disclaimer}</p>
    {/if}
  {/if}
</section>

<style>
  .list-heading {
    font-size: 1.05rem;
    margin: 0.25rem 0 0;
  }
  .filters {
    gap: 0.75rem 1rem;
    align-items: end;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    font-size: 0.85rem;
  }
  select {
    font: inherit;
    padding: 0.4rem 0.5rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
  }
  .chk {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.88rem;
    padding-bottom: 0.3rem;
  }
  .item {
    padding: 0.85rem 0.75rem;
    border-bottom: 1px solid var(--border);
  }
  .item:last-child {
    border-bottom: none;
  }
  .title {
    font-weight: 650;
    margin-top: 0.25rem;
  }
  .desc {
    margin: 0.35rem 0 0;
    font-size: 0.9rem;
  }
  .small {
    font-size: 0.85rem;
  }
  .cve {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }
  .badge.kev {
    border-color: var(--high);
    color: var(--high);
  }
  .badge.accent {
    border-color: var(--accent);
    color: var(--accent);
  }
  .links a {
    font-size: 0.82rem;
    font-family: var(--mono);
  }
  a.btn {
    display: inline-block;
    padding: 0.35rem 0.65rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-hover);
    color: var(--text);
    text-decoration: none;
    font-size: 0.85rem;
  }
  a.btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
