<script lang="ts">
  import { onMount } from "svelte";
  import SearchBox from "../components/SearchBox.svelte";
  import ResultList from "../components/ResultList.svelte";
  import { searchPreferRuleId, isSearchReady } from "../search";
  import { searchState, searchError, bootData, meta } from "../metaStore";
  import type { QuickLink, SearchDoc } from "../types";
  import { routes } from "../paths";
  import { formatDate } from "../format";
  import { fetchTagsCatalog } from "../api";

  let query = $state("");
  let results = $state<SearchDoc[]>([]);
  let ready = $state(false);
  let quickLinks = $state<QuickLink[]>([]);

  onMount(() => {
    bootData().then(() => {
      ready = isSearchReady();
      if (query) run(query);
    });
    fetchTagsCatalog()
      .then((c) => {
        quickLinks = c.quickLinks || [];
      })
      .catch(() => {
        quickLinks = [];
      });
  });

  function run(q: string) {
    query = q;
    if (!isSearchReady()) {
      results = [];
      return;
    }
    results = searchPreferRuleId(q, 50);
  }

  let sState = $derived($searchState);
  let sErr = $derived($searchError);
  let m = $derived($meta);
</script>

<section class="stack">
  <div>
    <h1>Search STIGs &amp; rules</h1>
    <p class="muted">
      Fast static reference for public DISA STIGs. Deep-link, copy, share.
    </p>
  </div>

  {#if quickLinks.length}
    <div>
      <div class="section-title" style="margin-top:0">
        <h2>Quick links</h2>
      </div>
      <div class="qlinks">
        {#each quickLinks as link (link.id)}
          {#if link.found && link.stigId}
            <a class="qlink" href={routes.stig(link.stigId)} title={link.stigName || link.label}>
              {link.label}
            </a>
          {:else}
            <span class="qlink missing" title="Not in current catalog">{link.label}</span>
          {/if}
        {/each}
      </div>
    </div>
  {/if}

  <SearchBox bind:value={query} autofocus={true} onsearch={run} />

  {#if sState === "loading"}
    <p class="state">Loading search index (~20k documents)…</p>
  {:else if sState === "error"}
    <p class="state error">Search unavailable: {sErr}</p>
  {:else if query.trim()}
    <div class="section-title">
      <h2>Results</h2>
      <span class="muted">{results.length} shown</span>
    </div>
    <ResultList {results} emptyLabel="No matches for that query." />
  {:else if ready && m}
    <div class="card muted">
      Index ready — {m.counts?.searchDocuments?.toLocaleString() ?? "?"} documents.
      Content last updated {formatDate(m.lastUpdated)}.
      Browse the <a href={routes.stigs()}>STIG catalog</a> with vendor / role filters, or try a rule ID
      like <span class="mono">SV-</span>.
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
    display: inline-block;
    padding: 0.4rem 0.7rem;
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
</style>
