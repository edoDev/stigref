<script lang="ts">
  import { onMount } from "svelte";
  import { routes } from "../paths";
  import { listNotes } from "../notes";
  import { getWatchlist, clearWatchlist, type WatchItem } from "../watchlist";
  import { bookmarks } from "../bookmarks";
  import {
    buildTeamPack,
    checklistToCsv,
    parseTeamPack,
    type TeamPack,
  } from "../teamPack";
  import { toast } from "../toast";
  import { copyText } from "../copy";
  import type { NoteEntry } from "../notes";

  let notes = $state<NoteEntry[]>([]);
  let watch = $state<WatchItem[]>([]);
  let packName = $state("My STIG pack");
  let importText = $state("");
  let mapYaml = $state(`product: windows-11
# B-017 map contribution helper — paste into intune_maps/
rules:
  - rule_id: SV-
    suggestions:
      - csp_id: Policy.
        value: ""
        confidence: medium
        kind: native
        rationale: 
`);

  onMount(() => {
    notes = listNotes();
    watch = getWatchlist();
  });

  let bm = $derived($bookmarks);

  function exportPack() {
    const rules = [
      ...bm.filter((b) => b.type === "rule").map((b) => ({ id: b.id, title: b.title })),
      ...watch.map((w) => ({ id: w.id, title: w.title })),
    ];
    const uniq = new Map(rules.map((r) => [r.id, r]));
    const pack = buildTeamPack(packName, [...uniq.values()]);
    const json = JSON.stringify(pack, null, 2);
    void copyText(json).then((ok) => toast(ok ? "Team pack JSON copied" : "Copy failed"));
  }

  function exportCsv() {
    const rows = [
      ...bm
        .filter((b) => b.type === "rule")
        .map((b) => {
          const n = notes.find((x) => x.type === "rule" && x.id === b.id);
          return {
            id: b.id,
            title: b.title,
            status: n?.status || "",
            note: n?.text || "",
          };
        }),
      ...watch.map((w) => {
        const n = notes.find((x) => x.type === "rule" && x.id === w.id);
        return {
          id: w.id,
          title: w.title,
          status: n?.status || "watch",
          note: n?.text || "",
        };
      }),
    ];
    const csv = checklistToCsv(rows);
    void copyText(csv).then((ok) => toast(ok ? "Checklist CSV copied" : "Copy failed"));
  }

  function doImport() {
    try {
      const pack: TeamPack = parseTeamPack(importText);
      toast(`Parsed pack “${pack.name}” with ${pack.rules.length} rules — open a rule to work it`);
    } catch (e) {
      toast(e instanceof Error ? e.message : String(e));
    }
  }

  function copyMap() {
    void copyText(mapYaml).then((ok) => toast(ok ? "YAML snippet copied" : "Copy failed"));
  }
</script>

<section class="stack">
  <div>
    <h1>Local tools</h1>
    <p class="muted">
      Browser-only helpers (B-017 / B-025 / B-037 / B-038 / B-052). Nothing is uploaded.
    </p>
  </div>

  <div class="card stack">
    <h2 class="h">Team pack &amp; checklist export</h2>
    <label class="field">
      <span class="muted">Pack name</span>
      <input type="text" bind:value={packName} />
    </label>
    <div class="row">
      <button type="button" class="primary" onclick={exportPack}>Copy team pack JSON</button>
      <button type="button" onclick={exportCsv}>Copy checklist CSV</button>
    </div>
    <p class="muted small" style="margin:0">
      Sources: {bm.filter((b) => b.type === "rule").length} bookmarked rules · {watch.length} watchlist
      · {notes.length} notes
    </p>
    <label class="field">
      <span class="muted">Import team pack JSON (validate only)</span>
      <textarea
        rows="4"
        bind:value={importText}
        placeholder="Paste stigref-team-pack/v1 JSON here"
      ></textarea>
    </label>
    <button type="button" onclick={doImport}>Validate import</button>
  </div>

  <div class="card stack">
    <h2 class="h">Watchlist (B-025)</h2>
    <p class="muted small" style="margin:0">
      Local list of rules to re-check after the next library release. Cross-release diff UI lands when
      two catalogs are present.
    </p>
    {#if watch.length === 0}
      <p class="muted" style="margin:0">Empty — toggle watch on a rule page.</p>
    {:else}
      <ul class="plain">
        {#each watch as w}
          <li><a href={routes.rule(w.id)}>{w.title || w.id}</a> <span class="mono muted">{w.id}</span></li>
        {/each}
      </ul>
      <button type="button" onclick={() => { clearWatchlist(); watch = []; }}>Clear watchlist</button>
    {/if}
  </div>

  <div class="card stack">
    <h2 class="h">Intune map YAML helper (B-017)</h2>
    <textarea rows="12" class="mono" bind:value={mapYaml}></textarea>
    <button type="button" onclick={copyMap}>Copy YAML</button>
    <p class="muted small" style="margin:0">
      Drop into <span class="mono">scripts/stigref_build/intune_maps/</span> — see
      <a href={routes.help()}>Help</a> / CONTRIBUTING_MAPS.
    </p>
  </div>
</section>

<style>
  .h {
    margin: 0;
    font-size: 1.05rem;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
  }
  input,
  textarea {
    font: inherit;
    padding: 0.45rem 0.55rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
  }
  textarea.mono {
    font-family: var(--mono);
    font-size: 0.82rem;
  }
  .small {
    font-size: 0.85rem;
  }
  .plain {
    margin: 0;
    padding-left: 1.1rem;
  }
</style>
