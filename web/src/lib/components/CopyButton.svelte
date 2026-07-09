<script lang="ts">
  import { copyText } from "../copy";
  import { toast } from "../toast";

  interface Props {
    text: string;
    label?: string;
    class?: string;
  }

  let { text, label = "Copy", class: className = "" }: Props = $props();
  let busy = $state(false);

  async function onClick() {
    if (!text || busy) return;
    busy = true;
    const ok = await copyText(text);
    toast(ok ? "Copied" : "Copy failed");
    busy = false;
  }
</script>

<button type="button" class={className} onclick={onClick} disabled={!text || busy}>
  {label}
</button>
