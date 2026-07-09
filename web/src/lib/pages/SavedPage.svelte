<script lang="ts">
  import { bookmarks, toggleBookmark, type Bookmark } from "../bookmarks";
  import { routes } from "../paths";

  let list = $derived($bookmarks);

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
