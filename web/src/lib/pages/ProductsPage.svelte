<script lang="ts">
  import { onMount } from "svelte";
  import { fetchIntuneIndex, fetchTagsCatalog } from "../api";
  import { routes } from "../paths";
  import type { IntuneProductIndex, LoadState, QuickLink } from "../types";
  import ErrorRetry from "../components/ErrorRetry.svelte";

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let links = $state<QuickLink[]>([]);
  let idx = $state<IntuneProductIndex | null>(null);

  async function loadProducts() {
    state = "loading";
    error = null;
    try {
      const [tags, products] = await Promise.all([
        fetchTagsCatalog(),
        fetchIntuneIndex(),
      ]);
      links = tags.quickLinks || [];
      idx = products;
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(() => {
    void loadProducts();
  });

  function cov(productId: string) {
    const p = idx?.products.find((x) => x.product === productId);
    if (!p?.rules) return "";
    const m = p.mappedRules ?? 0;
    return `${m}/${p.rules} (${Math.round((m / p.rules) * 100)}%)`;
  }
</script>

<section class="stack">
  <div>
    <h1>Products</h1>
    <p class="muted">Quick-link hubs with Intune coverage and export packs.</p>
  </div>

  {#if state === "loading"}
    <p class="state">Loading…</p>
  {:else if state === "error"}
    <ErrorRetry title="Could not load products" message={error} onretry={loadProducts} />
  {:else}
    <ul class="list card">
      {#each links as link (link.id)}
        <li>
          {#if link.found}
            <a class="item" href={routes.product(link.id)}>
              <div class="title">{link.label}</div>
              <div class="muted small">
                {link.stigName}
                {#if cov(link.id)}
                  · Intune {cov(link.id)}
                {/if}
              </div>
            </a>
          {:else}
            <div class="item muted">
              <div class="title">{link.label}</div>
              <div class="small">Not in current catalog</div>
            </div>
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .item {
    display: block;
    padding: 0.85rem 0.75rem;
    color: inherit;
    text-decoration: none;
    border-bottom: 1px solid var(--border);
  }
  .item:last-child {
    border-bottom: none;
  }
  a.item:hover {
    background: var(--bg-hover);
  }
  .title {
    font-weight: 650;
  }
  .small {
    font-size: 0.85rem;
    margin-top: 0.15rem;
  }
</style>
