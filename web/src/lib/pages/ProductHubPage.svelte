<script lang="ts">
  import { onMount } from "svelte";
  import { fetchIntuneIndex, fetchTagsCatalog, intuneProductUrl } from "../api";
  import { routes } from "../paths";
  import type { IntuneProductIndex, LoadState, QuickLink } from "../types";
  import { copyText } from "../copy";
  import { toast } from "../toast";
  import ErrorRetry from "../components/ErrorRetry.svelte";

  interface Props {
    id: string;
  }
  let { id }: Props = $props();

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let link = $state<QuickLink | null>(null);
  let product = $state<IntuneProductIndex["products"][0] | null>(null);
  let pack = $state<Record<string, unknown> | null>(null);

  async function load(productId: string) {
    state = "loading";
    error = null;
    pack = null;
    product = null;
    link = null;
    try {
      const [tags, idx] = await Promise.all([fetchTagsCatalog(), fetchIntuneIndex()]);
      link = (tags.quickLinks || []).find((q) => q.id === productId) || null;
      product = (idx.products || []).find((p) => p.product === productId) || null;
      if (!product && !link) {
        throw new Error(`Unknown product: ${productId}`);
      }
      if (productId) {
        const res = await fetch(intuneProductUrl(productId));
        if (res.ok) pack = await res.json();
      }
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  $effect(() => {
    void load(id);
  });

  async function copyCsv() {
    const csv = pack && (pack as { settingsCsv?: string }).settingsCsv;
    if (!csv) {
      toast("No CSV in pack");
      return;
    }
    toast((await copyText(csv)) ? "CSV copied" : "Copy failed");
  }

  async function copyReadme() {
    const r = pack && (pack as { readme?: string }).readme;
    if (!r) {
      toast("No readme");
      return;
    }
    toast((await copyText(r)) ? "Readme copied" : "Copy failed");
  }

  async function copyThreatSummary() {
    // B-069: product-level threat summary from pack settings + mapped rules
    const summary = {
      format: "stigref-product-threat-summary/v1",
      product: id,
      stigName: product?.stigName || link?.stigName,
      mappedRules: product?.mappedRules,
      rules: product?.rules,
      settings: product?.settings,
      disclaimer:
        "Aggregated export aid only. Not a vulnerability assessment. See rule threat panels for CVE/KEV/ATT&CK.",
      generatedAt: new Date().toISOString(),
    };
    toast(
      (await copyText(JSON.stringify(summary, null, 2)))
        ? "Threat summary JSON copied"
        : "Copy failed",
    );
  }

  let mapped = $derived(product?.mappedRules ?? 0);
  let total = $derived(product?.rules ?? 0);
  let pct = $derived(total ? Math.round((mapped / total) * 100) : 0);

  /** B-015: same OMA-URI with differing values across pack settings */
  let conflicts = $derived.by(() => {
    const settings = (pack as { settings?: Array<{ omaUri?: string; value?: string; name?: string; sourceRules?: string[] }> })
      ?.settings;
    if (!settings?.length) return [] as Array<{ omaUri: string; values: string[] }>;
    const byOma = new Map<string, Set<string>>();
    for (const s of settings) {
      const oma = s.omaUri || "";
      if (!oma) continue;
      if (!byOma.has(oma)) byOma.set(oma, new Set());
      byOma.get(oma)!.add(String(s.value ?? ""));
    }
    const out: Array<{ omaUri: string; values: string[] }> = [];
    for (const [omaUri, vals] of byOma) {
      if (vals.size > 1) out.push({ omaUri, values: [...vals] });
    }
    return out;
  });
</script>

<section class="stack">
  <p class="muted"><a href={routes.home()}>← Home</a></p>

  {#if state === "loading"}
    <p class="state">Loading product…</p>
  {:else if state === "error"}
    <ErrorRetry title="Could not load product" message={error} onretry={() => load(id)} />
  {:else}
    <div>
      <h1>{link?.label || id}</h1>
      <p class="muted">{link?.stigName || product?.stigName || ""}</p>
    </div>

    <div class="card stack">
      <h2 class="h">Intune map coverage</h2>
      <div class="bar">
        <div class="fill" style={`width:${pct}%`}></div>
      </div>
      <p class="muted" style="margin:0">
        {mapped} / {total} rules mapped ({pct}%) · {product?.settings ?? 0} unique settings
      </p>
      {#if link?.stigId}
        <p style="margin:0">
          <a href={routes.stig(link.stigId)}>Open STIG</a>
          ·
          <a href={intuneProductUrl(id)} target="_blank" rel="noopener">Raw export JSON</a>
        </p>
      {/if}
    </div>

    <div class="card stack">
      <h2 class="h">Apply in Intune (recipe)</h2>
      <ol class="steps">
        <li>Prefer <strong>Settings Catalog</strong> when the setting is available.</li>
        <li>
          Otherwise create a <strong>Windows custom (OMA-URI)</strong> configuration profile.
        </li>
        <li>Add each OMA-URI from the pack with the listed data type and value.</li>
        <li>ADMX-backed settings may need SyncML <span class="mono">&lt;enabled/&gt;</span> payloads — open Learn links on rule pages.</li>
        <li>Pilot on a pilot group; verify with STIG checks.</li>
      </ol>
      <div class="row">
        <button type="button" class="primary" onclick={copyCsv}>Copy settings CSV</button>
        <button type="button" onclick={copyReadme}>Copy pack README</button>
        <button type="button" onclick={copyThreatSummary}>Copy threat summary JSON</button>
      </div>
      <p class="muted small" style="margin:0">
        Assistive only — validate against STIG checks and current Microsoft documentation.
      </p>
    </div>

    {#if conflicts.length}
      <div class="card stack">
        <h2 class="h">Possible OMA-URI conflicts</h2>
        <p class="muted small" style="margin:0">
          Same OMA-URI appears with different suggested values across rules (B-015). Resolve before
          deploying a single profile.
        </p>
        <ul class="plain">
          {#each conflicts as c}
            <li>
              <span class="mono small">{c.omaUri}</span>
              <div class="muted small">values: {c.values.map((v) => JSON.stringify(v)).join(" · ")}</div>
            </li>
          {/each}
        </ul>
      </div>
    {/if}
  {/if}
</section>

<style>
  .h {
    margin: 0;
    font-size: 1.05rem;
  }
  .bar {
    height: 0.55rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 999px;
    overflow: hidden;
  }
  .fill {
    height: 100%;
    background: var(--accent);
  }
  .steps {
    margin: 0;
    padding-left: 1.2rem;
  }
  .steps li {
    margin: 0.35rem 0;
  }
  .small {
    font-size: 0.85rem;
  }
  .plain {
    margin: 0;
    padding-left: 1.1rem;
  }
</style>
