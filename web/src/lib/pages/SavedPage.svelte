<script lang="ts">
  import { onMount } from "svelte";
  import { bookmarks, toggleBookmark, type Bookmark } from "../bookmarks";
  import { routes } from "../paths";
  import { clearRecent, getRecent, type RecentItem } from "../recent";

  let list = $derived($bookmarks);
  let recent = $state<RecentItem[]>([]);

  onMount(() => {
    recent = getRecent();
  });

  function hrefFor(b: Bookmark): string {
    if (b.type === "rule") return routes.rule(b.id);
    if (b.type === "stig") return routes.stig(b.id);
    return `${routes.home()}?q=${encodeURIComponent(b.query || b.id)}`;
  }

  function remove(b: Bookmark) {
    toggleBookmark(b);
  }
</script>

<section class="stack">
  <div>
    <h1>Saved</h1>
    <p class="muted">Bookmarks stay in this browser only (localStorage).</p>
  </div>

  {#if recent.length}
    <div>
      <div class="section-title">
        <h2>Recently viewed</h2>
        <button type="button" onclick={() => { clearRecent(); recent = []; }}>Clear</button>
      </div>
      <ul class="list card">
        {#each recent as item (item.type + item.id)}
          <li class="row item">
            <span class="badge">{item.type}</span>
            <a href={item.type === "rule" ? routes.rule(item.id) : routes.stig(item.id)}
              >{item.title || item.id}</a
            >
          </li>
        {/each}
      </ul>
    </div>
  {/if}

  <h2>Bookmarks</h2>
  {#if list.length === 0}
    <p class="state">No bookmarks yet. Star a STIG or rule to save it here.</p>
  {:else}
    <ul class="list card">
      {#each list as b (b.type + b.id)}
        <li class="row item">
          <div class="grow">
            <span class="badge">{b.type}</span>
            <a href={hrefFor(b)}>{b.title || b.id}</a>
            <div class="mono muted small">{b.id}</div>
          </div>
          <button type="button" onclick={() => remove(b)}>Remove</button>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .item {
    padding: 0.75rem;
    border-bottom: 1px solid var(--border);
    justify-content: space-between;
  }
  .item:last-child {
    border-bottom: none;
  }
  .grow {
    flex: 1;
    min-width: 0;
  }
  .small {
    font-size: 0.8rem;
    margin-top: 0.15rem;
  }
</style>
