<script lang="ts">
  import { onMount } from "svelte";
  import { dataUrl, routes } from "../paths";
  import type { LoadState } from "../types";
  import ErrorRetry from "../components/ErrorRetry.svelte";
  import SearchBox from "../components/SearchBox.svelte";
  import {
    downloadText,
  } from "../exports";

  interface CisIndexRule {
    full_rule_id: string;
    title?: string;
    cisCount?: number;
    cisIds?: string[];
    profiles?: string[];
  }

  interface CisIndex {
    totalMappedRules?: number;
    mapFiles?: number;
    disclaimer?: string;
    rules?: CisIndexRule[];
  }

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let idx = $state<CisIndex | null>(null);
  let q = $state("");

  async function load() {
    state = "loading";
    error = null;
    try {
      const res = await fetch(dataUrl("cis", "index.json"));
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      idx = (await res.json()) as CisIndex;
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(() => {
    void load();
  });

  let filtered = $derived.by(() => {
    const list = idx?.rules || [];
    const needle = q.trim().toLowerCase();
    if (!needle) return list;
    return list.filter(
      (r) =>
        r.full_rule_id.toLowerCase().includes(needle) ||
        (r.title || "").toLowerCase().includes(needle) ||
        (r.cisIds || []).some((c) => c.toLowerCase().includes(needle)),
    );
  });

  function exportIndexCsv() {
    const rows = [["full_rule_id", "title", "cis_ids", "profiles", "cis_count"]];
    for (const r of filtered) {
      rows.push([
        r.full_rule_id,
        r.title || "",
        (r.cisIds || []).join(";"),
        (r.profiles || []).join(";"),
        String(r.cisCount ?? ""),
      ]);
    }
    const esc = (v: string) =>
      /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
    const csv = rows.map((row) => row.map(esc).join(",")).join("\n") + "\n";
    downloadText("stigref-cis-index.csv", csv, "text/csv;charset=utf-8");
  }

  function exportIndexMd() {
    const lines = [
      "# stigref CIS crosswalk index",
      "",
      `Mapped rules: ${idx?.totalMappedRules ?? 0}`,
      "",
      "| Rule | Title | CIS IDs | Profiles |",
      "| --- | --- | --- | --- |",
    ];
    for (const r of filtered) {
      lines.push(
        `| ${r.full_rule_id} | ${(r.title || "").replace(/\|/g, "/")} | ${(r.cisIds || []).join(", ")} | ${(r.profiles || []).join(", ")} |`,
      );
    }
    lines.push("", `> ${idx?.disclaimer || ""}`, "");
    downloadText(
      "stigref-cis-index.md",
      lines.join("\n"),
      "text/markdown;charset=utf-8",
    );
  }
</script>

<section class="stack">
  <div>
    <h1>CIS crosswalk</h1>
    <p class="muted">
      Curated STIG → CIS recommendation maps (public-safe IDs + notes). Full CIS Benchmark text is
      not redistributed — use CIS Workbench / your licensed PDF for assessment.
    </p>
  </div>

  {#if state === "loading"}
    <p class="state">Loading CIS index…</p>
  {:else if state === "error"}
    <ErrorRetry title="Could not load CIS index" message={error} onretry={load} />
    <p class="muted small">
      Run <span class="mono">python scripts/reapply_cis.py</span> after adding
      <span class="mono">cis_maps/*.yaml</span>.
    </p>
  {:else if idx}
    <div class="card muted">
      {idx.totalMappedRules?.toLocaleString() ?? 0} mapped rules · {idx.mapFiles ?? "?"} map file(s)
    </div>
    <SearchBox bind:value={q} placeholder="Filter by rule ID, title, or CIS ID…" />
    <div class="row">
      <button type="button" class="primary" onclick={exportIndexCsv}>Export CSV</button>
      <button type="button" onclick={exportIndexMd}>Export Markdown</button>
      <a class="btn" href={`${routes.home()}?cis=1`}>Search has-CIS</a>
    </div>
    <ul class="list card">
      {#each filtered as r (r.full_rule_id)}
        <li class="item">
          <a href={routes.rule(r.full_rule_id)}>{r.title || r.full_rule_id}</a>
          <div class="mono small">{r.full_rule_id}</div>
          <div class="muted small">
            CIS: {(r.cisIds || []).join(", ") || "—"}
            {#if r.profiles?.length}
              · {(r.profiles || []).join(", ")}
            {/if}
          </div>
        </li>
      {/each}
    </ul>
    {#if idx.disclaimer}
      <p class="muted small">{idx.disclaimer}</p>
    {/if}
  {/if}
</section>

<style>
  .item {
    padding: 0.65rem 0.75rem;
    border-bottom: 1px solid var(--border);
  }
  .item:last-child {
    border-bottom: none;
  }
  .small {
    font-size: 0.85rem;
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
</style>
