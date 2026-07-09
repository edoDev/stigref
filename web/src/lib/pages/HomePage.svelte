<script lang="ts">
  import { onMount } from "svelte";
  import SearchBox from "../components/SearchBox.svelte";
  import ResultList from "../components/ResultList.svelte";
  import { search, isSearchReady, emptyFilters, uniqueVendorsFromIndex } from "../search";
  import { searchState, searchError, bootData, meta } from "../metaStore";
  import type { IntuneProductIndex, QuickLink, SearchDoc, SearchFilters } from "../types";
  import { routes } from "../paths";
  import { formatDate } from "../format";
  import { fetchIntuneIndex, fetchTagsCatalog } from "../api";
  import { parseSearchParams, replaceSearchUrl } from "../urlState";

  let query = $state("");
  let filters = $state<SearchFilters>(emptyFilters());
  let results = $state<SearchDoc[]>([]);
  let ready = $state(false);
  let quickLinks = $state<QuickLink[]>([]);
  let intuneIndex = $state<IntuneProductIndex | null>(null);
  let vendors = $state<string[]>([]);

  function coverageFor(productId: string | null | undefined): string {
    if (!productId || !intuneIndex) return "";
    const p = intuneIndex.products.find((x) => x.product === productId);
    if (!p || !p.rules) return "";
    const mapped = p.mappedRules ?? 0;
    const pct = Math.round((mapped / p.rules) * 100);
    return `${mapped}/${p.rules} (${pct}%)`;
  }

  function run(q: string = query) {
    query = q;
    if (!isSearchReady()) {
      results = [];
      return;
    }
    const hasFilter =
      !!filters.type ||
      !!filters.severity ||
      !!filters.vendor ||
      filters.hasIntune ||
      filters.hasCve ||
      filters.inKev;
    if (!q.trim() && !hasFilter) {
      results = [];
    } else {
      results = search(q, 60, filters);
    }
    replaceSearchUrl(query, filters);
    vendors = uniqueVendorsFromIndex();
  }

  function clearFilters() {
    filters = emptyFilters();
    run(query);
  }

  onMount(() => {
    const parsed = parseSearchParams();
    query = parsed.q;
    filters = parsed.filters;

    bootData().then(() => {
      ready = isSearchReady();
      vendors = uniqueVendorsFromIndex();
      run(query);
    });
    fetchTagsCatalog()
      .then((c) => {
        quickLinks = c.quickLinks || [];
      })
      .catch(() => {
        quickLinks = [];
      });
    fetchIntuneIndex()
      .then((i) => {
        intuneIndex = i;
      })
      .catch(() => {
        intuneIndex = null;
      });
  });

  let sState = $derived($searchState);
  let sErr = $derived($searchError);
  let m = $derived($meta);

  let showResults = $derived(
    query.trim() ||
      filters.type ||
      filters.severity ||
      filters.vendor ||
      filters.hasIntune ||
      filters.hasCve ||
      filters.inKev,
  );
</script>

<section class="stack">
  <div>
    <h1>Search STIGs &amp; rules</h1>
    <p class="muted">
      Fast static reference for public DISA STIGs. Share filters via URL · deep-link · copy · Intune
      hints · CVE/KEV context.
    </p>
  </div>

  {#if quickLinks.length}
    <div>
      <div class="section-title" style="margin-top:0">
        <h2>Quick links</h2>
        <span class="muted">Intune map coverage</span>
      </div>
      <div class="qlinks">
        {#each quickLinks as link (link.id)}
          {#if link.found && link.stigId}
            <a class="qlink" href={routes.stig(link.stigId)} title={link.stigName || link.label}>
              <span>{link.label}</span>
              {#if coverageFor(link.id)}
                <span class="cov">{coverageFor(link.id)}</span>
              {/if}
            </a>
          {:else}
            <span class="qlink missing" title="Not in current catalog">{link.label}</span>
          {/if}
        {/each}
      </div>
    </div>
  {/if}

  <SearchBox bind:value={query} autofocus={true} onsearch={run} />

  <div class="filters card">
    <label class="field">
      <span class="muted">Type</span>
      <select
        bind:value={filters.type}
        onchange={() => run()}
      >
        <option value="">All</option>
        <option value="rule">Rules</option>
        <option value="stig">STIGs</option>
      </select>
    </label>
    <label class="field">
      <span class="muted">Severity</span>
      <select bind:value={filters.severity} onchange={() => run()}>
        <option value="">Any</option>
        <option value="high">high</option>
        <option value="medium">medium</option>
        <option value="low">low</option>
      </select>
    </label>
    <label class="field">
      <span class="muted">Vendor</span>
      <select bind:value={filters.vendor} onchange={() => run()}>
        <option value="">Any</option>
        {#each vendors as v}
          <option value={v}>{v}</option>
        {/each}
      </select>
    </label>
    <label class="chk">
      <input type="checkbox" bind:checked={filters.hasIntune} onchange={() => run()} />
      Has Intune map
    </label>
    <label class="chk">
      <input type="checkbox" bind:checked={filters.hasCve} onchange={() => run()} />
      Has CVE
    </label>
    <label class="chk">
      <input type="checkbox" bind:checked={filters.inKev} onchange={() => run()} />
      In CISA KEV
    </label>
    <button type="button" onclick={clearFilters}>Clear</button>
  </div>

  {#if sState === "loading"}
    <p class="state">Loading search index (~20k documents)…</p>
  {:else if sState === "error"}
    <p class="state error">Search unavailable: {sErr}</p>
  {:else if showResults}
    <div class="section-title">
      <h2>Results</h2>
      <span class="muted">{results.length} shown · URL updates as you filter</span>
    </div>
    <ResultList {results} emptyLabel="No matches for that query/filters." />
  {:else if ready && m}
    <div class="card muted">
      Index ready — {m.counts?.searchDocuments?.toLocaleString() ?? "?"} documents
      {#if m.counts?.rulesWithCve != null}
        · {m.counts.rulesWithCve.toLocaleString()} rules with CVE
      {/if}
      {#if m.counts?.rulesWithKev != null}
        · {m.counts.rulesWithKev.toLocaleString()} with KEV
      {/if}
      . Content last updated {formatDate(m.lastUpdated)}. Browse the
      <a href={routes.stigs()}>STIG catalog</a> or try a rule ID like
      <span class="mono">SV-</span>.
    </div>
  {/if}
</section>

<style>
  .qlinks {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
  }
  .qlink {
    display: inline-flex;
    flex-direction: column;
    gap: 0.15rem;
    padding: 0.45rem 0.75rem;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--chip, var(--bg-elevated));
    color: var(--text);
    font-size: 0.88rem;
    font-weight: 600;
    text-decoration: none;
  }
  .qlink:hover {
    border-color: var(--accent);
    color: var(--accent);
    text-decoration: none;
  }
  .qlink.missing {
    opacity: 0.45;
    cursor: not-allowed;
  }
  .cov {
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--text-muted);
  }
  .filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem 0.85rem;
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
    padding-bottom: 0.35rem;
  }
</style>
