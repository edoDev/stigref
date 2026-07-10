<script lang="ts">
  interface Props {
    title?: string;
    message?: string | null;
    onretry?: () => void;
    retryLabel?: string;
  }
  let {
    title = "Something went wrong",
    message = null,
    onretry,
    retryLabel = "Try again",
  }: Props = $props();
</script>

<div class="state error card" role="alert">
  <p class="title">{title}</p>
  {#if message}
    <p class="mono detail">{message}</p>
  {/if}
  {#if onretry}
    <p>
      <button type="button" class="primary" onclick={() => onretry()}>{retryLabel}</button>
    </p>
  {/if}
</div>

<style>
  .title {
    font-weight: 650;
    margin: 0 0 0.35rem;
  }
  .detail {
    margin: 0 0 0.75rem;
    font-size: 0.9rem;
    word-break: break-word;
  }
</style>
