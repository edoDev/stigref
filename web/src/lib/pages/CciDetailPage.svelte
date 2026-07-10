<script lang="ts">
  import { onMount } from "svelte";
  import { bootData } from "../metaStore";
  import { getAllDocs, isSearchReady } from "../search";
  import { buildCciIndex } from "../cciIndex";
  import { routes } from "../paths";
  import { severityClass } from "../format";

  interface Props {
    id: string;
  }
  let { id }: Props = $props();

  let rules = $state<Array<{ id: string; title: string; severity?: string }>>([]);
  let ready = $state(false);

  onMount(() => {
    bootData().then(() => {
      if (!isSearchReady()) return;
      const cci = id.toUpperCase();
      const entry = buildCciIndex(getAllDocs()).find((e) => e.cci === cci);
      rules = entry?.rules || [];
      ready = true;
    });
  });
</script>

<section class="stack">
  <p class="muted"><a href={routes.cci()}>← All CCIs</a></p>
  <h1 class="mono">{id}</h1>
  {#if !ready}
    <p class="state">Loading…</p>
  {:else if !rules.length}
    <p class="state">No rules in the current search index reference this CCI.</p>
  {:else}
    <p class="muted">{rules.length} rule(s)</p>
    <ul class="list card">
      {#each rules as r}
        <li class="item row">
          {#if r.severity}
            <span class={`badge ${severityClass(r.severity)}`}>{r.severity}</span>
          {/if}
          <a href={routes.rule(r.id)}>{r.title}</a>
          <span class="mono muted small">{r.id}</span>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .item {
    padding: 0.65rem 0.75rem;
    border-bottom: 1px solid var(--border);
    gap: 0.5rem;
  }
  .item:last-child {
    border-bottom: none;
  }
  .small {
    font-size: 0.8rem;
  }
</style>
