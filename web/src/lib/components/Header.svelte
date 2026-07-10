<script lang="ts">
  import { meta, metaState } from "../metaStore";
  import { routes } from "../paths";
  import { formatDate } from "../format";

  let m = $derived($meta);
  let state = $derived($metaState);
</script>

<header class="header">
  <div class="wrap row bar">
    <a class="brand" href={routes.home()}>stigref</a>
    <nav class="row nav">
      <a href={routes.home()}>Search</a>
      <a href={routes.stigs()}>STIGs</a>
      <a href={routes.products()}>Products</a>
      <a href={routes.kev()}>KEV</a>
      <a href={routes.saved()}>Saved</a>
      <a href={routes.help()}>Help</a>
      <a href={routes.about()}>About</a>
    </nav>
    <div class="meta muted">
      {#if state === "loading"}
        Loading catalog…
      {:else if state === "error"}
        Data unavailable
      {:else if m}
        {#if m.currentRelease || m.release?.label}
          <span class="rel">{m.release?.label || m.currentRelease}</span>
          ·
        {/if}
        Content updated {formatDate(m.lastUpdated)}
        {#if m.counts}
          · {m.counts.stigs ?? "?"} STIGs · {m.counts.rules ?? "?"} rules
        {/if}
      {/if}
    </div>
  </div>
</header>

<style>
  .header {
    border-bottom: 1px solid var(--border);
    background: var(--bg-elevated);
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .bar {
    min-height: 3.25rem;
    justify-content: space-between;
    gap: 0.75rem 1.25rem;
    padding-block: 0.55rem;
  }
  .brand {
    font-weight: 750;
    font-size: 1.15rem;
    color: var(--text);
    text-decoration: none;
    letter-spacing: -0.02em;
  }
  .brand:hover {
    color: var(--accent);
    text-decoration: none;
  }
  .nav {
    gap: 1rem;
  }
  .nav a {
    color: var(--text-muted);
    font-weight: 500;
  }
  .nav a:hover {
    color: var(--accent);
  }
  .meta {
    font-size: 0.82rem;
    margin-left: auto;
  }
  .rel {
    color: var(--accent);
    font-weight: 600;
  }
  @media (max-width: 720px) {
    .meta {
      width: 100%;
      order: 4;
      margin-left: 0;
    }
  }
</style>
