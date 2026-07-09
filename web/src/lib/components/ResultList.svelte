<script lang="ts">
  import type { SearchDoc } from "../types";
  import { href } from "../paths";
  import { severityClass } from "../format";

  interface Props {
    results: SearchDoc[];
    emptyLabel?: string;
  }

  let { results, emptyLabel = "No matches." }: Props = $props();

  function pathFor(doc: SearchDoc): string {
    const r = doc.route.startsWith("/") ? doc.route.slice(1) : doc.route;
    return href(...r.split("/"));
  }
</script>

{#if results.length === 0}
  <p class="state">{emptyLabel}</p>
{:else}
  <ul class="list card">
    {#each results as doc (doc.id)}
      <li>
        <a class="item" href={pathFor(doc)}>
          <div class="row">
            <span class="badge">{doc.type}</span>
            {#if doc.severity}
              <span class={`badge ${severityClass(doc.severity)}`}>{doc.severity}</span>
            {/if}
            {#if doc.inKev}
              <span class="badge kev">KEV</span>
            {/if}
            {#if doc.hasCve && !doc.inKev}
              <span class="badge">CVE</span>
            {/if}
            {#if doc.hasIntune}
              <span class="badge accent">intune</span>
            {/if}
            {#if doc.full_rule_id}
              <span class="mono muted">{doc.full_rule_id}</span>
            {/if}
          </div>
          <div class="title">{doc.title}</div>
          {#if doc.stig_names?.length}
            <div class="muted small">{doc.stig_names.join(" · ")}</div>
          {:else if doc.version}
            <div class="muted small">V{doc.version}R{doc.release}</div>
          {/if}
        </a>
      </li>
    {/each}
  </ul>
{/if}

<style>
  .title {
    font-weight: 600;
    margin-top: 0.2rem;
  }
  .small {
    font-size: 0.85rem;
    margin-top: 0.15rem;
  }
  .item {
    padding: 0.85rem 0.75rem !important;
  }
  .badge.kev {
    border-color: var(--high);
    color: var(--high);
  }
  .badge.accent {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
