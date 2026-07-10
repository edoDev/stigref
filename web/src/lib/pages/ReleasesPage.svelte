<script lang="ts">
  import { onMount } from "svelte";
  import { fetchMeta } from "../api";
  import { dataUrl, routes } from "../paths";
  import type { LoadState, Meta, ReleaseInfo } from "../types";
  import { formatDate } from "../format";
  import ErrorRetry from "../components/ErrorRetry.svelte";

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let meta = $state<Meta | null>(null);
  let reg = $state<{ currentRelease?: string; releases?: ReleaseInfo[] } | null>(null);
  let diffSummary = $state<string | null>(null);

  async function load() {
    state = "loading";
    error = null;
    try {
      meta = await fetchMeta();
      try {
        const res = await fetch(dataUrl("releases", "index.json"));
        if (res.ok) reg = await res.json();
      } catch {
        reg = null;
      }
      // Optional sample self-diff note
      diffSummary = null;
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(() => {
    void load();
  });

  let releases = $derived(
    (reg?.releases?.length ? reg.releases : meta?.releases) ||
      (meta?.release ? [meta.release] : []),
  );
  let current = $derived(meta?.currentRelease || reg?.currentRelease);
</script>

<section class="stack">
  <div>
    <h1>Releases &amp; changelog</h1>
    <p class="muted">
      Catalog releases registered in this build (B-021 / B-024). Full multi-quarter trees land on the
      next DISA library import; today the live tree is tagged with a release id.
    </p>
  </div>

  {#if state === "loading"}
    <div class="skeleton card" aria-busy="true">Loading release metadata…</div>
  {:else if state === "error"}
    <ErrorRetry title="Could not load releases" message={error} onretry={load} />
  {:else}
    <div class="card">
      <p style="margin:0">
        <strong>Current release:</strong>
        <span class="mono">{current || "—"}</span>
        {#if meta?.release?.label}
          · {meta.release.label}
        {/if}
      </p>
      {#if meta?.source?.filename}
        <p class="muted small" style="margin:0.35rem 0 0">
          Source: <span class="mono">{meta.source.filename}</span>
          {#if meta.source.sha256}
            · SHA-256 <span class="mono break">{meta.source.sha256.slice(0, 16)}…</span>
          {/if}
        </p>
      {/if}
      {#if meta?.builtAt}
        <p class="muted small" style="margin:0.25rem 0 0">
          Built {formatDate(meta.builtAt)} · content {formatDate(meta.lastUpdated)}
        </p>
      {/if}
    </div>

    <h2>Registered releases</h2>
    <ul class="list card">
      {#each releases as r (r.id)}
        <li class="item">
          <div class="row">
            <strong>{r.label || r.id}</strong>
            <span class="mono muted">{r.id}</span>
            {#if r.id === current}
              <span class="badge accent">current</span>
            {/if}
            {#if r.storage}
              <span class="badge">{r.storage}</span>
            {/if}
          </div>
          {#if r.sourceFile}
            <div class="muted small mono">{r.sourceFile}</div>
          {/if}
          {#if r.builtAt}
            <div class="muted small">Built {formatDate(r.builtAt)}</div>
          {/if}
        </li>
      {:else}
        <li class="item muted">No release registry entries yet.</li>
      {/each}
    </ul>

    <div class="card stack">
      <h2 class="h">What changed (B-022)</h2>
      <p class="muted" style="margin:0">
        Family-level diffs are produced with
        <span class="mono">python scripts/diff_releases.py --from … --to …</span>
        into <span class="mono">data/diffs/&#123;from&#125;__&#123;to&#125;.json</span>. When a second
        quarterly library is imported, this page will list those artifacts automatically.
      </p>
      {#if diffSummary}
        <pre class="block">{diffSummary}</pre>
      {/if}
      <p style="margin:0">
        <a href={routes.stigs()}>Browse STIG catalog</a>
        ·
        <a href={routes.about()}>Build provenance</a>
      </p>
    </div>
  {/if}
</section>

<style>
  .item {
    padding: 0.75rem;
    border-bottom: 1px solid var(--border);
  }
  .item:last-child {
    border-bottom: none;
  }
  .h {
    margin: 0;
    font-size: 1.05rem;
  }
  .small {
    font-size: 0.85rem;
  }
  .break {
    word-break: break-all;
  }
  .badge.accent {
    border-color: var(--accent);
    color: var(--accent);
  }
  .skeleton {
    min-height: 3rem;
    color: var(--text-muted);
  }
</style>
