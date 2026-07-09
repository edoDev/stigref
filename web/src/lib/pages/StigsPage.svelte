<script lang="ts">
  import { onMount } from "svelte";
  import { fetchStigIndex } from "../api";
  import { routes } from "../paths";
  import type { LoadState, StigIndexEntry } from "../types";
  import { formatDate } from "../format";
  import SearchBox from "../components/SearchBox.svelte";

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let stigs = $state<StigIndexEntry[]>([]);
  let filter = $state("");

  onMount(async () => {
    state = "loading";
    try {
      stigs = await fetchStigIndex();
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  });

  let filtered = $derived.by(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return stigs;
    return stigs.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        `v${s.version}r${s.release}`.includes(q) ||
        s.id.toLowerCase().includes(q),
    );
  });
</script>

<section class="stack">
  <div>
    <h1>STIG catalog</h1>
    <p class="muted">All STIGs/SRGs in the published data set.</p>
  </div>

  <SearchBox bind:value={filter} placeholder="Filter by name…" />

  {#if state === "loading"}
    <p class="state">Loading catalog…</p>
  {:else if state === "error"}
    <p class="state error">{error}</p>
  {:else}
    <div class="section-title">
      <h2>STIGs</h2>
      <span class="muted">{filtered.length} / {stigs.length}</span>
    </div>
    <ul class="list card">
      {#each filtered as s (s.id)}
        <li>
          <a class="item" href={routes.stig(s.id)}>
            <div class="title">{s.name}</div>
            <div class="muted small">
              V{s.version}R{s.release}
              · {s.rule_count} rules
              · {formatDate(s.release_date)}
            </div>
          </a>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .title {
    font-weight: 600;
  }
  .small {
    font-size: 0.85rem;
    margin-top: 0.15rem;
  }
  .item {
    padding: 0.85rem 0.75rem !important;
  }
</style>
