<script lang="ts">
  import { fetchStig } from "../api";
  import { routes } from "../paths";
  import type { LoadState, StigDetail } from "../types";
  import { formatDate, severityClass } from "../format";
  import CopyButton from "../components/CopyButton.svelte";
  import { stigCitation } from "../copy";

  interface Props {
    id: string;
  }
  let { id }: Props = $props();

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let stig = $state<StigDetail | null>(null);

  async function load(stigId: string) {
    state = "loading";
    error = null;
    stig = null;
    try {
      stig = await fetchStig(stigId);
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  $effect(() => {
    void load(id);
  });
</script>

<section class="stack">
  <p class="muted"><a href={routes.stigs()}>← All STIGs</a></p>

  {#if state === "loading"}
    <p class="state">Loading STIG…</p>
  {:else if state === "error"}
    <div class="state error">
      <p>Could not load STIG.</p>
      <p class="mono">{error}</p>
      <p><a href={routes.home()}>Back to search</a></p>
    </div>
  {:else if stig}
    <div class="row" style="justify-content: space-between; align-items: flex-start;">
      <div>
        <h1>{stig.name}</h1>
        <p class="muted">
          V{stig.version}R{stig.release}
          · released {formatDate(stig.release_date)}
          · {stig.rule_count} rules
        </p>
      </div>
      <CopyButton text={stigCitation(stig)} label="Copy citation" class="primary" />
    </div>

    {#if stig.description}
      <div class="card">
        <div class="section-title" style="margin-top:0">
          <h2>Description</h2>
          <CopyButton text={stig.description} label="Copy" />
        </div>
        <p style="margin:0">{stig.description}</p>
      </div>
    {/if}

    <div class="section-title">
      <h2>Rules</h2>
    </div>
    <ul class="list card">
      {#each stig.rules as r (r.full_rule_id)}
        <li>
          <a class="item" href={routes.rule(r.full_rule_id)}>
            <div class="row">
              {#if r.severity}
                <span class={`badge ${severityClass(r.severity)}`}>{r.severity}</span>
              {/if}
              <span class="mono muted">{r.full_rule_id}</span>
              {#if r.group_id}
                <span class="muted">({r.group_id})</span>
              {/if}
            </div>
            <div class="title">{r.title}</div>
          </a>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .title {
    font-weight: 600;
    margin-top: 0.2rem;
  }
  .item {
    padding: 0.85rem 0.75rem !important;
  }
</style>
