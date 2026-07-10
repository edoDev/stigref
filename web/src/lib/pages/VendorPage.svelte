<script lang="ts">
  import { onMount } from "svelte";
  import { fetchStigIndex } from "../api";
  import { routes } from "../paths";
  import type { LoadState, StigIndexEntry } from "../types";
  import ErrorRetry from "../components/ErrorRetry.svelte";
  import { formatDate } from "../format";

  interface Props {
    id: string;
  }
  let { id }: Props = $props();

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let stigs = $state<StigIndexEntry[]>([]);
  let vendorName = $derived(decodeURIComponent(id));

  async function load() {
    state = "loading";
    try {
      const all = await fetchStigIndex();
      stigs = all.filter((s) => (s.vendor || "Unknown") === vendorName);
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(() => {
    void load();
  });
</script>

<section class="stack">
  <p class="muted"><a href={routes.vendors()}>← Vendors</a></p>
  <h1>{vendorName}</h1>
  <p class="muted">{stigs.length} STIG(s) in current catalog</p>

  {#if state === "loading"}
    <p class="state">Loading…</p>
  {:else if state === "error"}
    <ErrorRetry title="Failed" message={error} onretry={load} />
  {:else}
    <ul class="list card">
      {#each stigs as s}
        <li class="item">
          <a href={routes.stig(s.id)}>{s.name}</a>
          <div class="muted small">
            V{s.version}R{s.release} · {s.rule_count} rules · {formatDate(s.release_date)}
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
  .small {
    font-size: 0.85rem;
  }
</style>
