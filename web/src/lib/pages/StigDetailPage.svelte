<script lang="ts">
  import { fetchStig } from "../api";
  import { routes } from "../paths";
  import type { LoadState, StigDetail } from "../types";
  import { formatDate, severityClass } from "../format";
  import CopyButton from "../components/CopyButton.svelte";
  import { stigCitation } from "../copy";
  import { intuneProductUrl } from "../api";
  import { bookmarks, toggleBookmark } from "../bookmarks";
  import { routes as appRoutes } from "../paths";

  interface Props {
    id: string;
  }
  let { id }: Props = $props();

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let stig = $state<StigDetail | null>(null);
  let saved = $derived($bookmarks.some((b) => b.type === "stig" && b.id === id));

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
          {#if stig.vendor}
            · {stig.vendor}
          {/if}
        </p>
        {#if stig.tags?.length}
          <div class="row" style="margin-top:0.35rem">
            {#each stig.roles || [] as r}
              <span class="badge">{r}</span>
            {/each}
            {#if stig.tags.includes("intune-companion")}
              <span class="badge">intune companion</span>
            {/if}
            {#if stig.tags.includes("gpo-companion")}
              <span class="badge">gpo companion</span>
            {/if}
            {#if stig.tags.includes("intune")}
              <span class="badge">intune</span>
            {/if}
          </div>
        {/if}
      </div>
      <div class="row">
        <button
          type="button"
          onclick={() =>
            toggleBookmark({ type: "stig", id: stig.id, title: stig.name })}
        >
          {saved ? "★ Saved" : "☆ Save"}
        </button>
        {#if stig.quicklink_id}
          <a class="btn" href={appRoutes.product(stig.quicklink_id)}>Product hub</a>
          <a class="btn" href={intuneProductUrl(stig.quicklink_id)} target="_blank" rel="noopener"
            >Export Intune JSON</a
          >
        {/if}
        <CopyButton text={stigCitation(stig)} label="Copy citation" class="primary" />
      </div>
    </div>

    {#if stig.quicklink_id}
      <div class="card muted" id="coverage">
        Product-level Intune draft (OMA-URI aggregate) for
        <span class="mono">{stig.quicklink_id}</span> — validate before deploy. Rule pages show
        per-setting CSP suggestions, CVE/KEV context, and copy packs. Coverage is computed at
        quarterly data build.
      </div>
    {/if}

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
  a.btn {
    display: inline-block;
    padding: 0.4rem 0.75rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-hover);
    color: var(--text);
    text-decoration: none;
    font-size: 0.9rem;
  }
  a.btn:hover {
    border-color: var(--accent);
    color: var(--accent);
    text-decoration: none;
  }
</style>
