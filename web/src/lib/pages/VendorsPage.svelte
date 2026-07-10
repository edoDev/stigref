<script lang="ts">
  import { onMount } from "svelte";
  import { fetchStigIndex } from "../api";
  import { routes } from "../paths";
  import type { LoadState, StigIndexEntry } from "../types";
  import ErrorRetry from "../components/ErrorRetry.svelte";

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let stigs = $state<StigIndexEntry[]>([]);

  async function load() {
    state = "loading";
    try {
      stigs = await fetchStigIndex();
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(() => {
    void load();
  });

  let vendors = $derived.by(() => {
    const m = new Map<string, number>();
    for (const s of stigs) {
      const v = s.vendor || "Unknown";
      m.set(v, (m.get(v) || 0) + 1);
    }
    return [...m.entries()]
      .map(([name, count]) => ({ name, count, slug: encodeURIComponent(name) }))
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
  });
</script>

<section class="stack">
  <div>
    <h1>Vendors</h1>
    <p class="muted">Product landings by vendor tag from the STIG catalog (B-049).</p>
  </div>

  {#if state === "loading"}
    <p class="state">Loading…</p>
  {:else if state === "error"}
    <ErrorRetry title="Failed to load vendors" message={error} onretry={load} />
  {:else}
    <ul class="list card">
      {#each vendors as v}
        <li class="item row">
          <a href={routes.vendor(v.name)}>{v.name}</a>
          <span class="muted">{v.count} STIG(s)</span>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .item {
    padding: 0.65rem 0.75rem;
    border-bottom: 1px solid var(--border);
    justify-content: space-between;
  }
  .item:last-child {
    border-bottom: none;
  }
</style>
