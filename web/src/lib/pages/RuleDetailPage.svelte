<script lang="ts">
  import { fetchRule } from "../api";
  import { routes } from "../paths";
  import type { LoadState, RuleDetail } from "../types";
  import { severityClass } from "../format";
  import CopyButton from "../components/CopyButton.svelte";
  import { ruleCitation } from "../copy";

  interface Props {
    id: string;
  }
  let { id }: Props = $props();

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let rule = $state<RuleDetail | null>(null);

  async function load(ruleId: string) {
    state = "loading";
    error = null;
    rule = null;
    try {
      rule = await fetchRule(ruleId);
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  $effect(() => {
    void load(id);
  });
</script>

<section class="stack">
  <p class="muted"><a href={routes.home()}>← Search</a></p>

  {#if state === "loading"}
    <p class="state">Loading rule…</p>
  {:else if state === "error"}
    <div class="state error">
      <p>Rule not found or failed to load.</p>
      <p class="mono">{error}</p>
      <p><a href={routes.home()}>Back to search</a></p>
    </div>
  {:else if rule}
    <div class="row" style="justify-content: space-between; align-items: flex-start;">
      <div>
        <div class="row">
          {#if rule.severity}
            <span class={`badge ${severityClass(rule.severity)}`}>{rule.severity}</span>
          {/if}
          <span class="mono">{rule.full_rule_id}</span>
        </div>
        <h1>{rule.title}</h1>
        <p class="muted">
          Group {rule.group_id}
          {#if rule.group_title}
            · {rule.group_title}
          {/if}
        </p>
      </div>
      <div class="row">
        <CopyButton text={rule.full_rule_id} label="Copy ID" />
        <CopyButton text={ruleCitation(rule)} label="Copy citation" class="primary" />
      </div>
    </div>

    {#if rule.stigs?.length}
      <div class="card">
        <h2 class="h">Appears in</h2>
        <ul class="plain">
          {#each rule.stigs as s}
            <li>
              <a href={routes.stig(s.id)}
                >{s.name} · V{s.version}R{s.release}</a
              >
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    <div class="card">
      <div class="section-title" style="margin-top:0">
        <h2 class="h">Check</h2>
        <CopyButton text={rule.check} label="Copy check" />
      </div>
      <pre class="block">{rule.check || "—"}</pre>
    </div>

    <div class="card">
      <div class="section-title" style="margin-top:0">
        <h2 class="h">Fix</h2>
        <CopyButton text={rule.fix} label="Copy fix" />
      </div>
      <pre class="block">{rule.fix || "—"}</pre>
    </div>

    {#if rule.ccis?.length || rule.cves?.length}
      <div class="card">
        <h2 class="h">Identifiers</h2>
        {#if rule.ccis?.length}
          <p><strong>CCI:</strong> <span class="mono">{rule.ccis.join(", ")}</span>
            <CopyButton text={rule.ccis.join(", ")} label="Copy" />
          </p>
        {/if}
        {#if rule.cves?.length}
          <p><strong>CVE:</strong> <span class="mono">{rule.cves.join(", ")}</span></p>
        {/if}
      </div>
    {/if}

    {#if rule.metadata?.VulnDiscussion}
      <div class="card">
        <div class="section-title" style="margin-top:0">
          <h2 class="h">Discussion</h2>
          <CopyButton text={String(rule.metadata.VulnDiscussion)} label="Copy" />
        </div>
        <pre class="block">{String(rule.metadata.VulnDiscussion)}</pre>
      </div>
    {/if}
  {/if}
</section>

<style>
  h1 {
    margin: 0.35rem 0;
    font-size: 1.35rem;
  }
  .h {
    margin: 0;
    font-size: 1rem;
  }
  .plain {
    margin: 0.35rem 0 0;
    padding-left: 1.1rem;
  }
</style>
