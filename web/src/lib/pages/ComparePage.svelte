<script lang="ts">
  import { onMount } from "svelte";
  import { fetchRule } from "../api";
  import { routes } from "../paths";
  import type { LoadState, RuleDetail } from "../types";
  import { severityClass } from "../format";
  import ErrorRetry from "../components/ErrorRetry.svelte";
  import CopyButton from "../components/CopyButton.svelte";

  let aId = $state("");
  let bId = $state("");
  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let a = $state<RuleDetail | null>(null);
  let b = $state<RuleDetail | null>(null);

  async function loadPair() {
    const sp = new URLSearchParams(location.search);
    aId = sp.get("a") || aId;
    bId = sp.get("b") || bId;
    if (!aId || !bId) {
      state = "idle";
      a = null;
      b = null;
      return;
    }
    state = "loading";
    error = null;
    try {
      const [ra, rb] = await Promise.all([fetchRule(aId), fetchRule(bId)]);
      a = ra;
      b = rb;
      state = "success";
      history.replaceState({}, "", routes.compare(a.full_rule_id, b.full_rule_id));
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  function run() {
    void loadPair();
  }

  onMount(() => {
    void loadPair();
  });

  function fieldDiff(label: string, left: string, right: string) {
    return { label, left: left || "—", right: right || "—", same: (left || "") === (right || "") };
  }

  let diffs = $derived.by(() => {
    if (!a || !b) return [];
    return [
      fieldDiff("Title", a.title, b.title),
      fieldDiff("Severity", a.severity, b.severity),
      fieldDiff("Group", a.group_id, b.group_id),
      fieldDiff("Check", a.check, b.check),
      fieldDiff("Fix", a.fix, b.fix),
      fieldDiff("CCIs", (a.ccis || []).join(", "), (b.ccis || []).join(", ")),
      fieldDiff("CVEs", (a.cves || []).join(", "), (b.cves || []).join(", ")),
    ];
  });
</script>

<section class="stack">
  <div>
    <h1>Compare rules</h1>
    <p class="muted">
      Side-by-side check/fix comparison (B-003). Paste two full rule IDs (e.g.
      <span class="mono">SV-…_rule</span>).
    </p>
  </div>

  <div class="card row filters">
    <label class="field grow">
      <span class="muted">Rule A</span>
      <input type="text" bind:value={aId} class="mono" placeholder="SV-…_rule" />
    </label>
    <label class="field grow">
      <span class="muted">Rule B</span>
      <input type="text" bind:value={bId} class="mono" placeholder="SV-…_rule" />
    </label>
    <button type="button" class="primary" onclick={run}>Compare</button>
  </div>

  {#if state === "loading"}
    <p class="state">Loading…</p>
  {:else if state === "error"}
    <ErrorRetry title="Compare failed" message={error} onretry={run} />
  {:else if a && b}
    <div class="grid">
      <div class="card">
        <div class="row">
          {#if a.severity}<span class={`badge ${severityClass(a.severity)}`}>{a.severity}</span>{/if}
          <a class="mono" href={routes.rule(a.full_rule_id)}>{a.full_rule_id}</a>
        </div>
        <h2>{a.title}</h2>
      </div>
      <div class="card">
        <div class="row">
          {#if b.severity}<span class={`badge ${severityClass(b.severity)}`}>{b.severity}</span>{/if}
          <a class="mono" href={routes.rule(b.full_rule_id)}>{b.full_rule_id}</a>
        </div>
        <h2>{b.title}</h2>
      </div>
    </div>

    {#each diffs as d}
      <div class="card stack" class:diff={!d.same}>
        <div class="section-title" style="margin:0">
          <h3 class="h">{d.label}</h3>
          {#if d.same}
            <span class="badge">same</span>
          {:else}
            <span class="badge review">differs</span>
          {/if}
          <CopyButton text={`### ${d.label}\nA:\n${d.left}\n\nB:\n${d.right}`} label="Copy pair" />
        </div>
        <div class="grid">
          <pre class="block">{d.left}</pre>
          <pre class="block">{d.right}</pre>
        </div>
      </div>
    {/each}
  {:else}
    <p class="muted state">Enter two rule IDs to compare.</p>
  {/if}
</section>

<style>
  .filters {
    align-items: end;
    gap: 0.75rem;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
  }
  .grow {
    flex: 1;
    min-width: 12rem;
  }
  input {
    font: inherit;
    padding: 0.45rem 0.55rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }
  h2 {
    margin: 0.35rem 0 0;
    font-size: 1.05rem;
  }
  .h {
    margin: 0;
    font-size: 1rem;
  }
  .diff {
    border-color: var(--medium);
  }
  .badge.review {
    border-color: var(--medium);
    color: var(--medium);
  }
  @media (max-width: 720px) {
    .grid {
      grid-template-columns: 1fr;
    }
  }
</style>
