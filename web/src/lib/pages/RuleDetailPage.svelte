<script lang="ts">
  import { fetchRule } from "../api";
  import { routes } from "../paths";
  import type { LoadState, RuleDetail, SearchDoc } from "../types";
  import { severityClass } from "../format";
  import CopyButton from "../components/CopyButton.svelte";
  import {
    ruleCitation,
    ruleMarkdown,
    ruleOmaUriPack,
  } from "../copy";
  import { bookmarks, toggleBookmark } from "../bookmarks";
  import ErrorRetry from "../components/ErrorRetry.svelte";
  import ConfidenceLegend from "../components/ConfidenceLegend.svelte";
  import { pushRecent } from "../recent";
  import { getAllDocs, isSearchReady } from "../search";
  import { meta } from "../metaStore";
  import { getNote, setNote } from "../notes";
  import { isWatched, toggleWatch } from "../watchlist";
  import { powershellHints } from "../psHints";
  import { toast } from "../toast";
  import { copyText } from "../copy";

  interface Props {
    id: string;
  }
  let { id }: Props = $props();

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let rule = $state<RuleDetail | null>(null);
  let related = $state<SearchDoc[]>([]);
  let noteText = $state("");
  let noteStatus = $state<"" | "todo" | "review" | "done" | "na">("");
  let watched = $state(false);
  let saved = $derived(
    $bookmarks.some((b) => b.type === "rule" && b.id === (rule?.full_rule_id || id)),
  );
  let m = $derived($meta);
  let psHints = $derived(rule ? powershellHints(rule) : []);

  function needsReview(rule: RuleDetail): boolean {
    const sugs = rule.intune?.suggestions || [];
    if (sugs.some((s) => (s.confidence || "").toLowerCase() === "low")) return true;
    if (sugs.some((s) => (s.source || "") === "heuristic" && (s.confidence || "") !== "high"))
      return true;
    return false;
  }

  function findRelated(r: RuleDetail): SearchDoc[] {
    if (!isSearchReady()) return [];
    const docs = getAllDocs().filter((d) => d.type === "rule");
    const gid = r.group_id;
    const ccis = new Set((r.ccis || []).map((c) => c.toUpperCase()));
    const out: SearchDoc[] = [];
    const seen = new Set<string>([r.full_rule_id]);
    for (const d of docs) {
      if (seen.has(d.full_rule_id || d.id)) continue;
      let score = 0;
      if (gid && d.group_id === gid) score += 2;
      for (const c of d.ccis || []) {
        if (ccis.has(c.toUpperCase())) score += 1;
      }
      if (score > 0) {
        out.push(d);
        seen.add(d.full_rule_id || d.id);
      }
      if (out.length >= 12) break;
    }
    return out.slice(0, 8);
  }

  async function load(ruleId: string) {
    state = "loading";
    error = null;
    rule = null;
    related = [];
    try {
      rule = await fetchRule(ruleId);
      state = "success";
      pushRecent({
        type: "rule",
        id: rule.full_rule_id,
        title: rule.title,
      });
      related = findRelated(rule);
      const n = getNote("rule", rule.full_rule_id);
      noteText = n?.text || "";
      noteStatus = (n?.status as typeof noteStatus) || "";
      watched = isWatched(rule.full_rule_id);
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  $effect(() => {
    void load(id);
  });

  function saveNote() {
    if (!rule) return;
    setNote("rule", rule.full_rule_id, noteText, noteStatus);
    toast("Note saved (this browser only)");
  }

  function onWatch() {
    if (!rule) return;
    watched = toggleWatch(rule.full_rule_id, rule.title);
    toast(watched ? "Added to watchlist" : "Removed from watchlist");
  }

  function embedSnippet(): string {
    if (!rule) return "";
    const url =
      typeof location !== "undefined"
        ? location.origin + routes.rule(rule.full_rule_id)
        : routes.rule(rule.full_rule_id);
    return `<blockquote cite="${url}">
  <strong>${rule.full_rule_id}</strong> — ${rule.title}
  <br/><a href="${url}">View on stigref</a>
</blockquote>`;
  }
</script>

<section class="stack">
  <p class="muted"><a href={routes.home()}>← Search</a></p>

  {#if state === "loading"}
    <div class="skeleton card" aria-busy="true">
      <div class="skel-line"></div>
      <div class="skel-line short"></div>
      <p class="state" style="margin:0.5rem 0 0">Loading rule…</p>
    </div>
  {:else if state === "error"}
    <ErrorRetry
      title="Rule not found or failed to load"
      message={error}
      onretry={() => load(id)}
    />
    <p class="muted"><a href={routes.home()}>Back to search</a></p>
  {:else if rule}
    <div class="row" style="justify-content: space-between; align-items: flex-start;">
      <div>
        <div class="row">
          {#if rule.severity}
            <span class={`badge ${severityClass(rule.severity)}`}>{rule.severity}</span>
          {/if}
          <span class="mono">{rule.full_rule_id}</span>
          {#if needsReview(rule)}
            <span class="badge review" title="Low-confidence or heuristic Intune mapping">
              Needs human review
            </span>
          {/if}
        </div>
        <h1>{rule.title}</h1>
        <p class="muted">
          Group {rule.group_id}
          {#if rule.group_title}
            · {rule.group_title}
          {/if}
        </p>
        {#if rule.checkAutomation?.checkStyle && rule.checkAutomation.checkStyle !== "unspecified"}
          <div class="row" style="margin-top:0.25rem">
            <span class="badge">{rule.checkAutomation.checkStyle}</span>
            {#if rule.checkAutomation.confidence}
              <span class="muted small">{rule.checkAutomation.confidence} confidence</span>
            {/if}
          </div>
        {/if}
      </div>
      <div class="row pack">
        <button
          type="button"
          aria-pressed={saved}
          aria-label={saved ? "Remove bookmark" : "Save bookmark"}
          onclick={() =>
            toggleBookmark({
              type: "rule",
              id: rule.full_rule_id,
              title: rule.title,
            })}
        >
          {saved ? "★ Saved" : "☆ Save"}
        </button>
        <button type="button" aria-pressed={watched} onclick={onWatch}>
          {watched ? "👁 Watching" : "Watch"}
        </button>
        <a class="btn" href={routes.compare(rule.full_rule_id, "")}>Compare…</a>
        <CopyButton text={rule.full_rule_id} label="Copy ID" />
        <CopyButton text={embedSnippet()} label="Embed HTML" />
        <CopyButton text={ruleCitation(rule)} label="Citation" class="primary" />
        <CopyButton text={ruleMarkdown(rule)} label="Markdown" />
        <CopyButton text={rule.check || ""} label="Check" />
        <CopyButton text={rule.fix || ""} label="Fix" />
        {#if ruleOmaUriPack(rule)}
          <CopyButton text={ruleOmaUriPack(rule)} label="OMA-URIs" />
        {/if}
        {#if rule.intune?.suggestions?.length}
          <CopyButton
            text={JSON.stringify(rule.intune.suggestions, null, 2)}
            label="Intune JSON"
          />
        {/if}
      </div>
    </div>

    {#if rule.packageEnrichment && (rule.packageEnrichment.ckl || rule.packageEnrichment.deviation)}
      <div class="card stack">
        <h2 class="h">DISA package mapping</h2>
        {#if rule.packageEnrichment.ckl}
          {@const ckl = rule.packageEnrichment.ckl}
          <div>
            <strong>Checklist (GPO package)</strong>
            {#if ckl.outsideGpoScope}
              <span class="badge">outside GPO scope</span>
            {/if}
            {#if ckl.siteSpecific}
              <span class="badge">site-specific</span>
            {/if}
            {#if ckl.gpoRefs?.length}
              <p style="margin:0.25rem 0 0">
                <span class="muted">GPO:</span>
                {ckl.gpoRefs.join(" · ")}
              </p>
            {/if}
            {#if ckl.intuneRefs?.length}
              <p style="margin:0.25rem 0 0">
                <span class="muted">Intune:</span>
                {ckl.intuneRefs.join(" · ")}
              </p>
            {/if}
            {#if ckl.comments && !ckl.gpoRefs?.length && !ckl.intuneRefs?.length}
              <pre class="block" style="margin-top:0.35rem">{ckl.comments}</pre>
            {/if}
            {#if ckl.sourceCkl}
              <p class="muted small" style="margin:0.25rem 0 0">Source: {ckl.sourceCkl}</p>
            {/if}
          </div>
        {/if}
        {#if rule.packageEnrichment.deviation}
          {@const d = rule.packageEnrichment.deviation}
          <div>
            <strong>Intune deviations workbook</strong>
            {#if d.notNativeToIntune}
              <span class="badge kev">not native to Intune</span>
            {/if}
            {#if d.falsePositiveScap}
              <span class="badge">SCAP false positive note</span>
            {/if}
            {#if d.explanation}
              <p style="margin:0.35rem 0 0">{d.explanation}</p>
            {/if}
            {#if d.cspRegistryPath}
              <p class="mono small" style="margin:0.25rem 0 0">{d.cspRegistryPath}</p>
            {/if}
            {#if d.sheet}
              <p class="muted small" style="margin:0.25rem 0 0">Sheet: {d.sheet}</p>
            {/if}
          </div>
        {/if}
        {#if rule.packageEnrichment.settingsCatalogProfiles?.length}
          <div>
            <strong>Related Settings Catalog profiles</strong>
            <ul class="plain">
              {#each rule.packageEnrichment.settingsCatalogProfiles as p}
                <li>{p.name} ({p.settingCount ?? "?"} settings)</li>
              {/each}
            </ul>
          </div>
        {/if}
      </div>
    {/if}

    {#if rule.threat && (rule.threat.cves?.length || rule.threat.attack?.length || rule.threat.status === "mapped" || rule.threat.status === "suggested")}
      <div class="card stack">
        <div class="section-title" style="margin-top:0">
          <h2 class="h">Threat context</h2>
          {#if rule.threat.inKev}
            <span class="badge kev">CISA KEV</span>
          {/if}
        </div>
        {#if rule.threat.cves?.length}
          <div class="row">
            {#each rule.threat.cves as c}
              <a
                class="cvechip"
                class:kev={c.inKev}
                href={c.nvdUrl}
                target="_blank"
                rel="noopener"
                title={c.inKev ? "In CISA KEV catalog" : "NVD"}
              >
                {c.id}{c.inKev ? " · KEV" : ""}
              </a>
            {/each}
          </div>
          {#if rule.threat.inKev}
            <p class="muted small" style="margin:0">
              At least one CVE is listed in the
              <a
                href="https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
                target="_blank"
                rel="noopener">CISA Known Exploited Vulnerabilities</a
              >
              catalog. Validate impact for your environment.
            </p>
          {/if}
        {:else}
          <p class="muted" style="margin:0">No CVE identifiers on this rule.</p>
        {/if}
        {#if rule.threat.attack?.length}
          <div>
            <strong class="small">MITRE ATT&amp;CK (suggested)</strong>
            <ul class="plain">
              {#each rule.threat.attack as t}
                <li>
                  <a href={t.url} target="_blank" rel="noopener"
                    >{t.techniqueId} — {t.name}</a
                  >
                  {#if t.confidence}
                    <span class="badge review">{t.confidence}</span>
                  {/if}
                </li>
              {/each}
            </ul>
            <p class="muted small" style="margin:0">
              Keyword/curated suggestions only — not authoritative mappings.
            </p>
          </div>
        {/if}
        {#if rule.threat.references?.length}
          <div>
            <strong class="small">Public reports / advisories</strong>
            <ul class="plain">
              {#each rule.threat.references as r}
                <li>
                  <a href={r.url} target="_blank" rel="noopener">{r.title}</a>
                  {#if r.type}
                    <span class="badge">{r.type}</span>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        {/if}
        {#if rule.threat.iocs?.length}
          <div>
            <strong class="small">Public IoCs</strong>
            <ul class="plain">
              {#each rule.threat.iocs as i}
                <li>
                  <span class="mono">{i.value}</span>
                  <span class="muted small">({i.type})</span>
                  {#if i.sourceUrl}
                    <a href={i.sourceUrl} target="_blank" rel="noopener">source</a>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        {/if}
        <p class="muted small" style="margin:0">
          {rule.threat.disclaimer ||
            "Public context only. Not a vulnerability scan result."}
        </p>
        <ConfidenceLegend compact />
      </div>
    {:else if rule.cves?.length}
      <div class="card stack">
        <h2 class="h">CVEs</h2>
        <div class="row">
          {#each rule.cves as c}
            <a
              class="cvechip"
              href={`https://nvd.nist.gov/vuln/detail/${c}`}
              target="_blank"
              rel="noopener">{c}</a
            >
          {/each}
        </div>
      </div>
    {/if}

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

    <div class="card check-card">
      <div class="section-title" style="margin-top:0">
        <h2 class="h">Check</h2>
        <CopyButton text={rule.check} label="Copy check" />
      </div>
      <p class="muted small section-label">How to verify compliance (assessment)</p>
      <pre class="block">{rule.check || "—"}</pre>
    </div>

    <div class="card fix-card">
      <div class="section-title" style="margin-top:0">
        <h2 class="h">Fix</h2>
        <CopyButton text={rule.fix} label="Copy fix" />
      </div>
      <p class="muted small section-label">Remediation guidance (not a finding by itself)</p>
      <pre class="block">{rule.fix || "—"}</pre>
    </div>

    {#if related.length}
      <div class="card stack">
        <h2 class="h">Related rules</h2>
        <p class="muted small" style="margin:0">Same group and/or shared CCI (from search index).</p>
        <ul class="plain">
          {#each related as d}
            <li>
              <a href={routes.rule(d.full_rule_id || d.id)}
                >{d.full_rule_id || d.id} — {d.title}</a
              >
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    <div class="card stack print-hide">
      <h2 class="h">Personal note (local)</h2>
      <label class="field">
        <span class="muted">Status</span>
        <select bind:value={noteStatus}>
          <option value="">—</option>
          <option value="todo">todo</option>
          <option value="review">review</option>
          <option value="done">done</option>
          <option value="na">n/a</option>
        </select>
      </label>
      <textarea rows="3" bind:value={noteText} placeholder="Scratch notes — never leave this browser"></textarea>
      <button type="button" onclick={saveNote}>Save note</button>
    </div>

    {#if psHints.length}
      <div class="card stack print-hide">
        <h2 class="h">Verify in Windows (PowerShell hints)</h2>
        <p class="muted small" style="margin:0">
          Operator aids only — STIG check text remains authoritative (B-020).
        </p>
        {#each psHints as h}
          <div>
            <strong class="small">{h.label}</strong>
            <pre class="block">{h.script}</pre>
            <CopyButton text={h.script} label="Copy script" />
          </div>
        {/each}
      </div>
    {/if}

    <div class="card stack print-hide">
      <h2 class="h">Tools &amp; provenance</h2>
      <p class="muted small" style="margin:0">
        Formal assessment workflows:
        <a href="https://github.com/NUWCDIVNPT/stig-manager" target="_blank" rel="noopener"
          >STIG Manager</a
        >
        ·
        <a
          href="https://public.cyber.mil/stigs/srg-stig-tools/"
          target="_blank"
          rel="noopener">DISA STIG Viewer / tools</a
        >
        ·
        <a href={routes.tools()}>Local tools</a>
      </p>
      {#if m}
        <p class="muted small" style="margin:0">
          Catalog {m.release?.label || m.currentRelease || "—"}
          {#if m.source?.filename}
            · <span class="mono">{m.source.filename}</span>
          {/if}
          {#if m.source?.sha256}
            · SHA <span class="mono">{m.source.sha256.slice(0, 12)}…</span>
          {/if}
        </p>
      {/if}
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

      <p class="muted small" style="margin:0">
        Curated / heuristic mappings — not an official Microsoft or DISA baseline. Validate in a
        pilot ring before production.
      </p>
      <ConfidenceLegend compact />

      <details class="recipe">
        <summary>How to apply in Intune</summary>
        <ol>
          <li>Prefer <strong>Settings Catalog</strong> if the setting exists there.</li>
          <li>
            Else: <strong>Devices → Configuration → Create → Windows 10 and later → Templates →
              Custom</strong>.
          </li>
          <li>Add each OMA-URI below (name, OMA-URI, type, value).</li>
          <li>
            ADMX-backed settings may need SyncML <span class="mono">&lt;enabled/&gt;</span> style
            payloads — open the Learn link for the setting.
          </li>
          <li>Assign to a pilot group; verify with the STIG check text.</li>
        </ol>
      </details>

      {#if !rule.intune}
        <p class="muted" style="margin:0">
          No Intune analysis for this rule (outside Microsoft / quick-link processing scope).
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
                {#if (s.confidence || "").toLowerCase() === "low" || s.source === "heuristic"}
                  <span class="badge review">review</span>
                {/if}
              </div>
              <div class="sug-title">{s.title}</div>
              {#if s.settingsCatalogName}
                <div class="small">
                  <strong>Settings Catalog:</strong> {s.settingsCatalogName}
                </div>
              {/if}
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
  .badge.review {
    border-color: var(--medium);
    color: var(--medium);
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
  }
  select,
  textarea {
    font: inherit;
    padding: 0.4rem 0.5rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
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
  .check-card {
    border-left: 3px solid var(--accent);
  }
  .fix-card {
    border-left: 3px solid var(--medium);
  }
  .section-label {
    margin: 0 0 0.35rem;
  }
  .skeleton .skel-line {
    height: 0.75rem;
    background: var(--bg-hover);
    border-radius: 4px;
    margin-bottom: 0.45rem;
    animation: pulse 1.2s ease-in-out infinite;
  }
  .skeleton .skel-line.short {
    width: 50%;
  }
  @keyframes pulse {
    0%,
    100% {
      opacity: 0.45;
    }
    50% {
      opacity: 1;
    }
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
  .pack {
    justify-content: flex-end;
    max-width: 22rem;
  }
  .cvechip {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    border: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 0.82rem;
    color: var(--text);
    text-decoration: none;
  }
  .cvechip:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
  .cvechip.kev {
    border-color: var(--high);
    color: var(--high);
  }
  .badge.kev {
    border-color: var(--high);
    color: var(--high);
  }
  .recipe {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    background: var(--bg);
    font-size: 0.9rem;
  }
  .recipe summary {
    cursor: pointer;
    font-weight: 600;
  }
  .recipe ol {
    margin: 0.5rem 0 0;
    padding-left: 1.2rem;
  }
</style>
