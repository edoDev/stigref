<script lang="ts">
  import { onMount } from "svelte";
  import { fetchStigIndex, fetchTagsCatalog } from "../api";
  import { routes } from "../paths";
  import type { LoadState, StigIndexEntry, TagsCatalog } from "../types";
  import { formatDate } from "../format";
  import SearchBox from "../components/SearchBox.svelte";

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let stigs = $state<StigIndexEntry[]>([]);
  let catalog = $state<TagsCatalog | null>(null);
  let filter = $state("");
  let vendor = $state("");
  let role = $state("");
  let special = $state(""); // tag id from filterHints.special

  onMount(async () => {
    state = "loading";
    try {
      const [idx, tags] = await Promise.all([fetchStigIndex(), fetchTagsCatalog()]);
      stigs = idx;
      catalog = tags;
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  });

  let filtered = $derived.by(() => {
    const q = filter.trim().toLowerCase();
    return stigs.filter((s) => {
      if (vendor && s.vendor !== vendor) return false;
      if (role && !(s.roles || []).includes(role)) return false;
      if (special) {
        const tag = catalog?.filterHints?.special?.find((x) => x.id === special)?.tag;
        if (tag && !(s.tags || []).includes(tag)) return false;
      }
      if (!q) return true;
      return (
        s.name.toLowerCase().includes(q) ||
        `v${s.version}r${s.release}`.includes(q) ||
        s.id.toLowerCase().includes(q) ||
        (s.vendor || "").toLowerCase().includes(q) ||
        (s.tags || []).some((t) => t.toLowerCase().includes(q))
      );
    });
  });

  function clearFilters() {
    vendor = "";
    role = "";
    special = "";
    filter = "";
  }

  let vendors = $derived(catalog?.vendors || []);
  let roles = $derived(catalog?.filterHints?.roles || catalog?.roles || []);
  let specials = $derived(catalog?.filterHints?.special || []);
</script>

<section class="stack">
  <div>
    <h1>STIG catalog</h1>
    <p class="muted">Filter by vendor, role, or companion-content tags.</p>
  </div>

  <SearchBox bind:value={filter} placeholder="Filter by name, vendor, tag…" />

  <div class="filters card">
    <label class="field">
      <span class="muted">Vendor</span>
      <select bind:value={vendor}>
        <option value="">All vendors</option>
        {#each vendors as v}
          <option value={v}>{v}</option>
        {/each}
      </select>
    </label>
    <label class="field">
      <span class="muted">Role</span>
      <select bind:value={role}>
        <option value="">All roles</option>
        {#each roles as r}
          <option value={r}>{r}</option>
        {/each}
      </select>
    </label>
    <label class="field">
      <span class="muted">Tags</span>
      <select bind:value={special}>
        <option value="">Any</option>
        {#each specials as s}
          <option value={s.id}>{s.label}</option>
        {/each}
      </select>
    </label>
    <button type="button" onclick={clearFilters}>Clear</button>
  </div>

  <div class="chiprow">
    <button type="button" class:active={role === "server"} onclick={() => (role = role === "server" ? "" : "server")}>
      Server
    </button>
    <button
      type="button"
      class:active={role === "workstation"}
      onclick={() => (role = role === "workstation" ? "" : "workstation")}
    >
      Workstation
    </button>
    <button type="button" class:active={role === "browser"} onclick={() => (role = role === "browser" ? "" : "browser")}>
      Browser
    </button>
    <button
      type="button"
      class:active={special === "intune-companion"}
      onclick={() => (special = special === "intune-companion" ? "" : "intune-companion")}
    >
      Intune companion
    </button>
    <button
      type="button"
      class:active={special === "gpo-companion"}
      onclick={() => (special = special === "gpo-companion" ? "" : "gpo-companion")}
    >
      GPO companion
    </button>
    <button type="button" class:active={vendor === "Microsoft"} onclick={() => (vendor = vendor === "Microsoft" ? "" : "Microsoft")}>
      Microsoft
    </button>
  </div>

  {#if state === "loading"}
    <p class="state">Loading catalog…</p>
  {:else if state === "error"}
    <p class="state error">{error}</p>
  {:else}
    <div class="section-title">
      <h2>STIGs</h2>
      <span class="muted">{filtered.length} / {stigs.length}</span>
    </div>
    <ul class="list card">
      {#each filtered as s (s.id)}
        <li>
          <a class="item" href={routes.stig(s.id)}>
            <div class="row">
              {#if s.vendor}
                <span class="badge">{s.vendor}</span>
              {/if}
              {#each (s.roles || []).slice(0, 2) as r}
                <span class="badge">{r}</span>
              {/each}
              {#if s.tags?.includes("intune-companion")}
                <span class="badge accent">intune</span>
              {/if}
              {#if s.tags?.includes("gpo-companion")}
                <span class="badge accent">gpo</span>
              {/if}
            </div>
            <div class="title">{s.name}</div>
            <div class="muted small">
              V{s.version}R{s.release}
              · {s.rule_count} rules
              · {formatDate(s.release_date)}
            </div>
          </a>
        </li>
      {/each}
    </ul>
    {#if filtered.length === 0}
      <p class="state">No STIGs match these filters.</p>
    {/if}
  {/if}
</section>

<style>
  .title {
    font-weight: 600;
    margin-top: 0.25rem;
  }
  .small {
    font-size: 0.85rem;
    margin-top: 0.15rem;
  }
  .item {
    padding: 0.85rem 0.75rem !important;
  }
  .filters {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 0.75rem;
    align-items: end;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
  }
  select {
    font: inherit;
    padding: 0.45rem 0.5rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
  }
  .chiprow {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }
  .chiprow button {
    border-radius: 999px;
    font-size: 0.85rem;
  }
  .chiprow button.active {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--chip, var(--bg-hover));
  }
  .badge.accent {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
