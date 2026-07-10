<script lang="ts">
  import { meta, metaState, metaError } from "../metaStore";
  import { formatDate } from "../format";
  import { routes } from "../paths";

  let m = $derived($meta);
  let state = $derived($metaState);
  let err = $derived($metaError);
</script>

<section class="stack">
  <h1>About stigref</h1>
  <div class="card stack">
    <p style="margin:0">
      <strong>stigref</strong> is a static STIG reference browser: search public DISA
      STIGs/SRGs, open deep links, and copy check/fix text cleanly. It is
      <em>not</em> an assessment tool (see
      <a href="https://github.com/NUWCDIVNPT/stig-manager" rel="noopener" target="_blank"
        >STIG Manager</a
      >
      for that).
    </p>
    <p class="muted" style="margin:0">
      Hosted as a static site. Data is rebuilt from the public
      <code class="mono">U_</code> SRG-STIG library ZIP (no CUI content).
    </p>
    <p style="margin:0">
      <a href={routes.help()}>Help &amp; walkthroughs</a>
      ·
      <a href={routes.home()}>Search</a>
    </p>
  </div>

  <div class="card stack">
    <h2 style="margin:0">Appearance</h2>
    <p class="muted" style="margin:0">
      Fixed <strong>Carbon Green</strong> theme (dark SOC-style palette). Theme switching was removed
      for a consistent product look.
    </p>
  </div>

  <div class="card stack">
    <h2 style="margin:0">Tags &amp; Intune</h2>
    <p class="muted" style="margin:0">
      Vendors and roles are inferred from STIG titles. Companion tags like
      <span class="mono">intune-companion</span> and <span class="mono">gpo-companion</span> are
      curated: public library ZIPs usually contain XCCDF + PDFs only, not Intune JSON templates.
      The Intune MDM STIG itself is tagged <span class="mono">intune</span>.
    </p>
  </div>

  <div class="card">
    <h2>Catalog metadata</h2>
    {#if state === "loading"}
      <p class="muted">Loading…</p>
    {:else if state === "error"}
      <p class="error">Failed to load meta.json: {err}</p>
    {:else if m}
      <dl class="dl">
        <dt>Release</dt>
        <dd>
          {m.release?.label || m.currentRelease || "—"}
          {#if m.currentRelease}
            <span class="mono muted">({m.currentRelease})</span>
          {/if}
        </dd>
        <dt>Content last updated</dt>
        <dd>{formatDate(m.lastUpdated)} <span class="mono muted">({m.lastUpdated})</span></dd>
        <dt>Built at</dt>
        <dd class="mono">{m.builtAt || "—"}</dd>
        <dt>Source file</dt>
        <dd class="mono">{m.source?.filename || "—"}</dd>
        <dt>Source SHA-256</dt>
        <dd class="mono break">{m.source?.sha256 || "—"}</dd>
        <dt>Counts</dt>
        <dd>
          {m.counts?.stigs ?? "?"} STIGs · {m.counts?.rules ?? "?"} rules ·
          {m.counts?.searchDocuments ?? "?"} search docs
        </dd>
        {#if m.sizes?.totalMB != null}
          <dt>Data size (raw)</dt>
          <dd>
            {m.sizes.totalMB} MB · {m.sizes.totalFiles?.toLocaleString() ?? "?"} files
            <span class="muted"> (uncompressed on disk)</span>
          </dd>
        {/if}
        <dt>Generator</dt>
        <dd class="mono">{m.generator || "—"}</dd>
      </dl>
    {/if}
  </div>
</section>

<style>
  .dl {
    display: grid;
    grid-template-columns: 11rem 1fr;
    gap: 0.45rem 1rem;
    margin: 0;
  }
  dt {
    color: var(--text-muted);
    font-size: 0.9rem;
  }
  dd {
    margin: 0;
  }
  .break {
    word-break: break-all;
  }
  h2 {
    margin-top: 0;
    font-size: 1.05rem;
  }
  @media (max-width: 600px) {
    .dl {
      grid-template-columns: 1fr;
    }
  }
</style>
