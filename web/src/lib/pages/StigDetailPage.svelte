<script lang="ts">
  import { fetchStig } from "../api";
  import { dataUrl, routes } from "../paths";
  import type { LoadState, StigDetail } from "../types";
  import { formatDate, severityClass } from "../format";
  import CopyButton from "../components/CopyButton.svelte";
  import { stigCitation } from "../copy";
  import { intuneProductUrl } from "../api";
  import { bookmarks, toggleBookmark } from "../bookmarks";
  import { routes as appRoutes } from "../paths";
  import ErrorRetry from "../components/ErrorRetry.svelte";
  import { pushRecent } from "../recent";

  interface Props {
    id: string;
  }
  let { id }: Props = $props();

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let stig = $state<StigDetail | null>(null);
  let familySiblings = $state<
    Array<{ id: string; name: string; version: string; release: string; release_date?: string }>
  >([]);
  let saved = $derived($bookmarks.some((b) => b.type === "stig" && b.id === id));

  async function load(stigId: string) {
    state = "loading";
    error = null;
    stig = null;
    familySiblings = [];
    try {
      stig = await fetchStig(stigId);
      state = "success";
      pushRecent({ type: "stig", id: stig.id, title: stig.name });
      // B-023: other versions in same family
      if (stig.family) {
        try {
          const res = await fetch(dataUrl("families", "index.json"));
          if (res.ok) {
            const body = await res.json();
            const fam = (body.families || []).find(
              (f: { family: string }) => f.family === stig!.family,
            );
            if (fam?.versions?.length) {
              familySiblings = fam.versions.filter(
                (v: { id: string }) => v.id !== stig!.id,
              );
            }
          }
        } catch {
          /* ignore */
        }
      }
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
    <ErrorRetry title="Could not load STIG" message={error} onretry={() => load(id)} />
    <p class="muted"><a href={routes.home()}>Back to search</a></p>
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
        <div class="row" style="margin-top:0.35rem">
          {#each stig.roles || [] as r}
            <span class="badge">{r}</span>
          {/each}
          {#if stig.automation?.hasGpoPackage}
            <span class="badge accent">DISA GPO package</span>
          {/if}
          {#if stig.automation?.hasIntunePackage}
            <span class="badge accent">DISA Intune package</span>
          {/if}
          {#if stig.automation?.shbRelated}
            <span class="badge">SHB-related</span>
          {/if}
          {#if stig.automation?.manualOrPlatformNative}
            <span class="badge">Manual / platform-native</span>
          {/if}
          {#if stig.tags?.includes("intune")}
            <span class="badge">intune STIG</span>
          {/if}
        </div>
      </div>
      <div class="row">
        <button
          type="button"
          aria-pressed={saved}
          aria-label={saved ? "Remove bookmark" : "Save bookmark"}
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

    {#if familySiblings.length}
      <div class="card stack">
        <h2 style="margin:0;font-size:1rem">Other versions in catalog</h2>
        <p class="muted small" style="margin:0">
          Same family key (<span class="mono">{stig.family}</span>). Multi-release storage will
          expand this list across quarterly libraries.
        </p>
        <ul class="plain">
          {#each familySiblings as v}
            <li>
              <a href={routes.stig(v.id)}
                >{v.name} · V{v.version}R{v.release}</a
              >
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    {#if stig.automation}
      <div class="card stack">
        <h2 style="margin:0;font-size:1rem">Automation &amp; packages</h2>
        {#if stig.automation.hasGpoPackage}
          <p style="margin:0">
            <strong>DISA GPO package:</strong>
            {(stig.automation.gpoProducts || []).join("; ") || "yes"}
          </p>
        {:else}
          <p class="muted" style="margin:0">
            No matching product found in the quarterly DISA STIG GPO package (or package not present
            under <span class="mono">raw/</span>).
          </p>
        {/if}
        {#if stig.automation.hasIntunePackage}
          <p style="margin:0">
            <strong>DISA Intune package profiles:</strong>
            {(stig.automation.intuneProfiles || [])
              .slice(0, 6)
              .map((p) => p.name)
              .join("; ") || "yes"}
          </p>
        {:else}
          <p class="muted" style="margin:0">
            No matching DISA Intune policy JSON for this STIG in the quarterly Intune package.
          </p>
        {/if}
        {#if stig.automation.shbRelated}
          <p style="margin:0">
            <strong>SHB-related:</strong> commonly included in DoD Secure Host Baseline–style Windows
            host stacks (Win10/11 + browser + Defender + firewall + Office/Reader). Not an official SHB
            matrix.
          </p>
        {/if}
        {#if stig.automation.manualOrPlatformNative}
          <p style="margin:0">
            <strong>Manual / platform-native:</strong> no DISA GPO/Intune host package matched —
            {#if stig.automation.platformKind}
              classified as <span class="mono">{stig.automation.platformKind}</span>.
            {:else}
              often appliance/app-specific or checklist-manual.
            {/if}
          </p>
        {/if}
      </div>
    {/if}

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
