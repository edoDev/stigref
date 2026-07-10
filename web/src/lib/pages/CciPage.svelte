<script lang="ts">
  import { onMount } from "svelte";
  import { bootData, searchState } from "../metaStore";
  import { getAllDocs, isSearchReady } from "../search";
  import { buildCciIndex, type CciEntry } from "../cciIndex";
  import { routes } from "../paths";
  import SearchBox from "../components/SearchBox.svelte";

  let q = $state("");
  let entries = $state<CciEntry[]>([]);
  let ready = $state(false);

  function rebuild() {
    if (!isSearchReady()) return;
    entries = buildCciIndex(getAllDocs());
    ready = true;
  }

  onMount(() => {
    bootData().then(rebuild);
  });

  let filtered = $derived.by(() => {
    const needle = q.trim().toUpperCase();
    if (!needle) return entries.slice(0, 200);
    return entries
      .filter(
        (e) =>
          e.cci.includes(needle) ||
          e.rules.some((r) => r.id.toUpperCase().includes(needle) || r.title.toUpperCase().includes(needle)),
      )
      .slice(0, 200);
  });

  let sState = $derived($searchState);
</script>

<section class="stack">
  <div>
    <h1>CCI browser</h1>
    <p class="muted">
      CCI → rules (built from the search index, B-027). Showing up to 200 matches.
    </p>
  </div>

  <SearchBox bind:value={q} placeholder="Filter CCI-… or rule title…" />

  {#if sState === "loading" || !ready}
    <p class="state">Building CCI index…</p>
  {:else}
    <p class="muted">{filtered.length.toLocaleString()} of {entries.length.toLocaleString()} CCIs</p>
    <ul class="list card">
      {#each filtered as e (e.cci)}
        <li class="item">
          <a class="mono cci" href={routes.cciId(e.cci)}>{e.cci}</a>
          <span class="muted">{e.count} rule(s)</span>
          <div class="muted small">
            {e.rules
              .slice(0, 3)
              .map((r) => r.id)
              .join(" · ")}
            {#if e.count > 3}
              …
            {/if}
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .item {
    padding: 0.65rem 0.75rem;
    border-bottom: 1px solid var(--border);
  }
  .item:last-child {
    border-bottom: none;
  }
  .cci {
    font-weight: 650;
    color: var(--accent);
    text-decoration: none;
  }
  .small {
    font-size: 0.82rem;
    margin-top: 0.2rem;
  }
</style>
