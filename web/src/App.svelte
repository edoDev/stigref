<script lang="ts">
  import { onMount } from "svelte";
  import Header from "./lib/components/Header.svelte";
  import HomePage from "./lib/pages/HomePage.svelte";
  import StigsPage from "./lib/pages/StigsPage.svelte";
  import StigDetailPage from "./lib/pages/StigDetailPage.svelte";
  import RuleDetailPage from "./lib/pages/RuleDetailPage.svelte";
  import AboutPage from "./lib/pages/AboutPage.svelte";
  import KevPage from "./lib/pages/KevPage.svelte";
  import SavedPage from "./lib/pages/SavedPage.svelte";
  import ProductsPage from "./lib/pages/ProductsPage.svelte";
  import ProductHubPage from "./lib/pages/ProductHubPage.svelte";
  import HelpPage from "./lib/pages/HelpPage.svelte";
  import ReleasesPage from "./lib/pages/ReleasesPage.svelte";
  import ComparePage from "./lib/pages/ComparePage.svelte";
  import CciPage from "./lib/pages/CciPage.svelte";
  import CciDetailPage from "./lib/pages/CciDetailPage.svelte";
  import VendorsPage from "./lib/pages/VendorsPage.svelte";
  import VendorPage from "./lib/pages/VendorPage.svelte";
  import ToolsPage from "./lib/pages/ToolsPage.svelte";
  import NistPage from "./lib/pages/NistPage.svelte";
  import CisPage from "./lib/pages/CisPage.svelte";
  import { initRouter, route } from "./lib/router";
  import { bootData } from "./lib/metaStore";
  import { toastMessage } from "./lib/toast";
  import { routes, baseUrl } from "./lib/paths";
  import { initTheme } from "./lib/theme";
  import { initKeyboard } from "./lib/keyboard";

  let r = $derived($route);
  let toast = $derived($toastMessage);

  onMount(() => {
    initTheme();
    const stopRouter = initRouter();
    const stopKeys = initKeyboard();
    bootData();
    // B-042: offline shell (caches app assets; data stays network-first)
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register(`${baseUrl()}sw.js`).catch(() => {
        /* optional in dev */
      });
    }
    return () => {
      stopRouter();
      stopKeys();
    };
  });
</script>

<a class="skip-link" href="#main-content">Skip to main content</a>
<Header />

<main id="main-content" class="wrap" tabindex="-1">
  {#if r.name === "home"}
    <HomePage />
  {:else if r.name === "about"}
    <AboutPage />
  {:else if r.name === "stigs"}
    <StigsPage />
  {:else if r.name === "stig"}
    {#key r.id}
      <StigDetailPage id={r.id} />
    {/key}
  {:else if r.name === "rule"}
    {#key r.id}
      <RuleDetailPage id={r.id} />
    {/key}
  {:else if r.name === "kev"}
    <KevPage />
  {:else if r.name === "saved"}
    <SavedPage />
  {:else if r.name === "products"}
    <ProductsPage />
  {:else if r.name === "product"}
    {#key r.id}
      <ProductHubPage id={r.id} />
    {/key}
  {:else if r.name === "help"}
    <HelpPage />
  {:else if r.name === "releases"}
    <ReleasesPage />
  {:else if r.name === "compare"}
    <ComparePage />
  {:else if r.name === "cci"}
    <CciPage />
  {:else if r.name === "cciDetail"}
    {#key r.id}
      <CciDetailPage id={r.id} />
    {/key}
  {:else if r.name === "vendors"}
    <VendorsPage />
  {:else if r.name === "vendor"}
    {#key r.id}
      <VendorPage id={r.id} />
    {/key}
  {:else if r.name === "tools"}
    <ToolsPage />
  {:else if r.name === "nist"}
    <NistPage />
  {:else if r.name === "cis"}
    <CisPage />
  {:else}
    <section class="state error" role="alert">
      <h1>Not found</h1>
      <p>No page for <span class="mono">{r.path}</span></p>
      <p><a href={routes.home()}>Go home</a></p>
    </section>
  {/if}
</main>

<footer class="footer">
  <div class="wrap muted">
    stigref — static STIG reference ·
    <a href="https://github.com/edoDev/stigref" rel="noopener" target="_blank">GitHub</a>
  </div>
</footer>

{#if toast}
  <div class="toast" role="status">{toast}</div>
{/if}

<style>
  .footer {
    border-top: 1px solid var(--border);
    padding: 1rem 0 1.5rem;
    font-size: 0.85rem;
  }
</style>
