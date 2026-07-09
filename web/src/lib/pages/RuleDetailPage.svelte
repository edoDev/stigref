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

    <div class="card stack">
      <div class="section-title" style="margin-top:0">
        <h2 class="h">Intune / CSP suggestions</h2>
        {#if rule.intune?.suggestions?.length}
          <CopyButton
            text={JSON.stringify(rule.intune.suggestions, null, 2)}
            label="Copy suggestions JSON"
          />
        {/if}
      </div>
      {#if !rule.intune}
        <p class="muted" style="margin:0">
          No Intune analysis for this rule (only quick-link products are processed in v1).
          <a
            href="https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-configuration-service-provider"
            target="_blank"
            rel="noopener">Policy CSP index</a
          >
        </p>
      {:else if rule.intune.status === "unmapped" || !rule.intune.suggestions?.length}
        <p class="muted" style="margin:0">
          {rule.intune.message || "No Intune CSP mapping yet for this rule."}
        </p>
        <p style="margin:0">
          <a href={rule.intune.policySearchUrl || "https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-configuration-service-provider"} target="_blank" rel="noopener"
            >Search Policy CSP docs</a
          >
          · contribute maps in
          <span class="mono">scripts/stigref_build/intune_maps/</span>
        </p>
      {:else}
        {#if rule.intune.multiOption}
          <p class="muted" style="margin:0">
            Multiple options — there is not always a 1:1 GPO/ADMX → native CSP mapping.
          </p>
        {/if}
        <ul class="sug">
          {#each rule.intune.suggestions as s}
            <li class="sug-item">
              <div class="row">
                <span class="badge">{s.kind || "csp"}</span>
                <span class="badge">{s.confidence || "?"} conf</span>
                <span class="badge">{s.source || ""}</span>
              </div>
              <div class="sug-title">{s.title}</div>
              {#if s.omaUri}
                <div class="mono small">{s.omaUri}</div>
              {/if}
              {#if s.value != null && s.value !== ""}
                <div class="small"><strong>Value:</strong> <span class="mono">{s.value}</span>
                  <CopyButton text={String(s.value)} label="Copy value" />
                </div>
              {/if}
              {#if s.rationale}
                <div class="muted small">{s.rationale}</div>
              {/if}
              <div class="row" style="margin-top:0.35rem">
                {#if s.omaUri}
                  <CopyButton text={s.omaUri} label="Copy OMA-URI" />
                {/if}
                {#if s.learnUrl}
                  <a class="btn" href={s.learnUrl} target="_blank" rel="noopener">Learn / usage</a>
                {/if}
              </div>
            </li>
          {/each}
        </ul>
      {/if}
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
  .sug {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .sug-item {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem;
    background: var(--bg);
  }
  .sug-title {
    font-weight: 650;
    margin-top: 0.35rem;
  }
  .small {
    font-size: 0.88rem;
    margin-top: 0.25rem;
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
  a.btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
