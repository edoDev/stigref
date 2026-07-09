<script lang="ts">
  interface Props {
    value?: string;
    placeholder?: string;
    autofocus?: boolean;
    onsearch?: (q: string) => void;
  }

  let {
    value = $bindable(""),
    placeholder = "Search STIGs, rule IDs, titles…",
    autofocus = false,
    onsearch,
  }: Props = $props();

  function emit() {
    onsearch?.(value);
  }
</script>

<form
  class="search"
  onsubmit={(e) => {
    e.preventDefault();
    emit();
  }}
>
  <input
    type="search"
    bind:value
    {placeholder}
    autocomplete="off"
    spellcheck="false"
    oninput={() => emit()}
    aria-label="Search"
    {@attach (el) => {
      if (autofocus && el instanceof HTMLInputElement) {
        queueMicrotask(() => el.focus());
      }
    }}
  />
</form>

<style>
  .search {
    width: 100%;
  }
</style>
