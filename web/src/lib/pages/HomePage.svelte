<script lang="ts">
  import { onMount } from "svelte";
  import SearchBox from "../components/SearchBox.svelte";
  import ResultList from "../components/ResultList.svelte";
  import ErrorRetry from "../components/ErrorRetry.svelte";
  import {
    searchAsync,
    isSearchReady,
    emptyFilters,
    uniqueVendorsFromIndex,
  } from "../search";
  import { searchState, searchError, bootData, meta } from "../metaStore";
  import type { IntuneProductIndex, QuickLink, SearchDoc, SearchFilters } from "../types";
  import { routes } from "../paths";
  import { formatDate } from "../format";
  import { fetchIntuneIndex, fetchTagsCatalog } from "../api";
  import { parseSearchParams, replaceSearchUrl } from "../urlState";
  import { debounce } from "../debounce";
  import { getRecent } from "../recent";
  import type { RecentItem } from "../recent";

  let query = $state("");
  let filters = $state<SearchFilters>(emptyFilters());
  let results = $state<SearchDoc[]>([]);
  let ready = $state(false);
  let quickLinks = $state<QuickLink[]>([]);
  let intuneIndex = $state<IntuneProductIndex | null>(null);
  let vendors = $state<string[]>([]);
  let recent = $state<RecentItem[]>([]);

  function coverageFor(productId: string | null | undefined): string {
    if (!productId || !intuneIndex) return "";
    const p = intuneIndex.products.find((x) => x.product === productId);
    if (!p || !p.rules) return "";
    const mapped = p.mappedRules ?? 0;
    const pct = Math.round((mapped / p.rules) * 100);
    return `${mapped}/${p.rules} (${pct}%)`;
  }

  /** Immediate search results; URL sync is debounced. */
  async function runResults(q: string = query) {
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
      filters.inKev ||
      filters.hasAttack ||
      filters.hasCis ||
      filters.hasOval ||
      filters.hasScap;
    if (!q.trim() && !hasFilter) {
      results = [];
    } else {
      results = await searchAsync(q, 60, filters);
    }
    vendors = uniqueVendorsFromIndex();
  }

  const debouncedUrl = debounce(() => {
    replaceSearchUrl(query, filters);
  }, 250);

  function run(q: string = query) {
    void runResults(q);
    debouncedUrl();
  }

  function clearFilters() {
    filters = emptyFilters();
    run(query);
  }

  function retryBoot() {
    bootData(true).then(() => {
      ready = isSearchReady();
      vendors = uniqueVendorsFromIndex();
      run(query);
    });
  }

  function clearTypeFilter() {
    filters = { ...filters, type: "" };
    run(query);
  }

  onMount(() => {
    const parsed = parseSearchParams();
    query = parsed.q;
    filters = parsed.filters;
    recent = getRecent();

    bootData().then(async () => {
      ready = isSearchReady();
      vendors = uniqueVendorsFromIndex();
      await runResults(query);
      // Initial URL may already match; still sync cleanly once
      replaceSearchUrl(query, filters);
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

    return () => debouncedUrl.cancel();
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
      filters.inKev ||
      filters.hasAttack ||
      filters.hasCis ||
      filters.hasOval ||
      filters.hasScap,
  );

  let liveMsg = $derived(
    sState === "loading"
      ? "Loading search index"
      : sState === "error"
        ? "Search unavailable"
        : showResults
          ? `${results.length} result${results.length === 1 ? "" : "s"}`
          : ready
            ? "Index ready"
            : "",
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
            <a class="qlink" href={routes.product(link.id)} title={link.stigName || link.label}>
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
        <option value="srg">SRGs</option>
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
    <label class="chk">
      <input type="checkbox" bind:checked={filters.hasAttack} onchange={() => run()} />
      Has ATT&amp;CK
    </label>
    <label class="chk">
      <input type="checkbox" bind:checked={filters.hasCis} onchange={() => run()} />
      Has CIS map
    </label>
    <label class="chk">
      <input type="checkbox" bind:checked={filters.hasOval} onchange={() => run()} />
      OVAL signal
    </label>
    <label class="chk">
      <input type="checkbox" bind:checked={filters.hasScap} onchange={() => run()} />
      SCAP signal
    </label>
    <button type="button" onclick={clearFilters}>Clear</button>
  </div>

  <div class="sr-only" role="status" aria-live="polite" aria-atomic="true">{liveMsg}</div>

  {#if sState === "loading"}
    <div class="skeleton card" aria-busy="true">
      <div class="skel-line"></div>
      <div class="skel-line short"></div>
      <p class="state" style="margin:0.5rem 0 0">Loading search index (~20k documents)…</p>
    </div>
  {:else if sState === "error"}
    <ErrorRetry
      title="Search unavailable"
      message={sErr}
      onretry={retryBoot}
    />
  {:else if showResults}
    <div class="section-title">
      <h2 id="search-results-heading">Results</h2>
      <span class="muted">{results.length} shown · URL updates as you filter</span>
    </div>
    {#if results.length === 0 && query.trim()}
      <div class="card" role="status">
        <p style="margin:0">
          <strong>No matches</strong> for
          <span class="mono">{query.trim()}</span>
          {#if filters.type}
            with type filter <span class="mono">{filters.type}</span>
          {/if}.
        </p>
        <ul class="muted" style="margin:0.5rem 0 0; padding-left:1.2rem">
          {#if filters.type === "stig"}
            <li>
              Terms like <em>BitLocker</em> or <em>print</em> usually appear on
              <strong>rules</strong>, not STIG titles.
              <button type="button" class="linkish" onclick={clearTypeFilter}>
                Search all types
              </button>
            </li>
          {/if}
          {#if filters.hasIntune || filters.hasCve || filters.inKev || filters.hasCis || filters.hasAttack || filters.hasOval || filters.hasScap || filters.severity || filters.vendor}
            <li>
              Active facet filters may be hiding hits.
              <button type="button" class="linkish" onclick={clearFilters}>Clear filters</button>
            </li>
          {/if}
          <li>
            Catalog filter on
            <a href={routes.stigs()}>STIGs</a> only matches STIG <em>names</em> — use this home
            search for rule text.
          </li>
        </ul>
      </div>
    {/if}
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
      <a href={routes.stigs()}>STIG catalog</a>,
      <a href={routes.insights()}>Library Observatory</a>, or try a rule ID like
      <span class="mono">SV-</span>.
      <span class="kbd-hint"> Press <kbd>/</kbd> to focus search · <kbd>?</kbd> help</span>
    </div>
    {#if recent.length}
      <div>
        <div class="section-title">
          <h2>Recently viewed</h2>
          <span class="muted">This browser only</span>
        </div>
        <ul class="recent card">
          {#each recent.slice(0, 8) as item (item.type + item.id)}
            <li>
              <span class="badge">{item.type}</span>
              <a href={item.type === "rule" ? routes.rule(item.id) : routes.stig(item.id)}
                >{item.title || item.id}</a
              >
            </li>
          {/each}
        </ul>
      </div>
    {/if}
  {/if}
</section>

<style>
  button.linkish {
    background: none;
    border: none;
    color: var(--accent);
    padding: 0;
    font: inherit;
    text-decoration: underline;
    cursor: pointer;
  }
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
  .recent {
    list-style: none;
    margin: 0;
    padding: 0.5rem 0.75rem;
  }
  .recent li {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    padding: 0.35rem 0;
    border-bottom: 1px solid var(--border);
  }
  .recent li:last-child {
    border-bottom: none;
  }
  .kbd-hint {
    display: inline;
  }
  kbd {
    font-family: var(--mono);
    font-size: 0.8em;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.05rem 0.3rem;
    background: var(--bg);
  }
  .skeleton .skel-line {
    height: 0.75rem;
    background: var(--bg-hover);
    border-radius: 4px;
    margin-bottom: 0.45rem;
    animation: pulse 1.2s ease-in-out infinite;
  }
  .skeleton .skel-line.short {
    width: 55%;
  }
  @keyframes pulse {
    0%,
    100% {
      opacity: 0.45;
    }
    50% {
      opacity: 1;
    }
  }
</style>
