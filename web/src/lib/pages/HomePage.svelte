<script lang="ts">
  import { onMount } from "svelte";
  import SearchBox from "../components/SearchBox.svelte";
  import ResultList from "../components/ResultList.svelte";
  import { searchPreferRuleId, isSearchReady } from "../search";
  import { searchState, searchError, bootData, meta } from "../metaStore";
  import type { SearchDoc } from "../types";
  import { routes } from "../paths";
  import { formatDate } from "../format";

  let query = $state("");
  let results = $state<SearchDoc[]>([]);
  let ready = $state(false);

  onMount(() => {
    bootData().then(() => {
      ready = isSearchReady();
      if (query) run(query);
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
      Browse the <a href={routes.stigs()}>STIG catalog</a> or try a rule ID like
      <span class="mono">SV-</span>.
    </div>
  {/if}
</section>
