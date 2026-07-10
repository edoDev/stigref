<script lang="ts">
  import { onMount } from "svelte";
  import { dataUrl, routes } from "../paths";
  import type { InsightsDoc, LoadState } from "../types";
  import { formatDate } from "../format";
  import { copyText } from "../copy";
  import { toast } from "../toast";
  import ErrorRetry from "../components/ErrorRetry.svelte";
  import {
    insightsBoardMarkdown,
    insightsIntuneCsv,
    insightsScorecardsCsv,
  } from "../insightsExport";

  let state = $state<LoadState>("idle");
  let error = $state<string | null>(null);
  let doc = $state<InsightsDoc | null>(null);
  let tab = $state<
    "landscape" | "intune" | "automation" | "crosswalk" | "threat" | "health"
  >("landscape");

  async function load() {
    state = "loading";
    error = null;
    try {
      const res = await fetch(dataUrl("stats", "insights.json"));
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      doc = (await res.json()) as InsightsDoc;
      state = "success";
    } catch (e) {
      state = "error";
      error = e instanceof Error ? e.message : String(e);
    }
  }

  onMount(() => {
    void load();
  });

  let k = $derived(doc?.kpis ?? {});
  let sev = $derived(doc?.severity ?? {});
  let sevTotal = $derived(
    (sev.high || 0) + (sev.medium || 0) + (sev.low || 0) + (sev.unknown || 0),
  );

  function barPct(n: number, max: number): string {
    if (!max) return "0%";
    return `${Math.max(2, Math.round((100 * n) / max))}%`;
  }

  function share(n: number | undefined, d: number): string {
    if (!d || !n) return "0%";
    return `${Math.round((100 * n) / d)}%`;
  }

  async function exportBoard() {
    if (!doc) return;
    const md = insightsBoardMarkdown(doc, `${location.origin}${routes.insights()}`);
    toast((await copyText(md)) ? "Board pack Markdown copied" : "Copy failed");
  }

  async function exportIntuneCsv() {
    if (!doc) return;
    toast((await copyText(insightsIntuneCsv(doc))) ? "Intune CSV copied" : "Copy failed");
  }

  async function exportScorecardsCsv() {
    if (!doc) return;
    toast(
      (await copyText(insightsScorecardsCsv(doc))) ? "Scorecards CSV copied" : "Copy failed",
    );
  }

  let maxVendorRules = $derived(
    Math.max(1, ...(doc?.vendors || []).slice(0, 12).map((v) => v.rules)),
  );
  let maxCci = $derived(Math.max(1, ...(doc?.cci?.top || []).slice(0, 15).map((c) => c.ruleCount)));
  let maxAttack = $derived(
    Math.max(1, ...(doc?.attack?.techniques || []).slice(0, 15).map((t) => t.ruleCount)),
  );
  let maxKevYear = $derived(Math.max(1, ...(doc?.kev?.byYear || []).map((y) => y.count)));
  let maxLandscape = $derived(Math.max(1, ...(doc?.landscape || []).slice(0, 40).map((l) => l.rules)));
  let autoStigs = $derived(doc?.automation?.stigs || {});
  let autoStigsTotal = $derived(
    (autoStigs.both || 0) +
      (autoStigs.gpoPackage || 0) +
      (autoStigs.intunePackage || 0) +
      (autoStigs.neither || 0),
  );
  let autoRules = $derived(doc?.automation?.rules || {});
  let maxRoleRules = $derived(
    Math.max(1, ...(doc?.roles || []).map((x) => x.rules)),
  );
  let maxCisProduct = $derived(
    Math.max(1, ...(doc?.cis?.byProduct || []).map((x) => x.rules)),
  );
</script>

<section class="stack insights">
  <div class="head row" style="justify-content: space-between; align-items: flex-start">
    <div>
      <h1>Library Observatory</h1>
      <p class="muted" style="margin: 0.25rem 0 0; max-width: 52rem">
        Precomputed metrics from the public STIG library, Intune maps, CIS crosswalk, CCI density,
        ATT&amp;CK seeds, and CISA KEV. Not a compliance score or vulnerability assessment.
      </p>
      {#if doc}
        <p class="muted small" style="margin: 0.35rem 0 0">
          Release <span class="mono">{doc.releaseId || "—"}</span>
          · generated {formatDate(doc.generatedAt || "")}
        </p>
      {/if}
    </div>
    <div class="row pack print-hide">
      <button type="button" class="primary" onclick={exportBoard} disabled={!doc}>
        Copy board pack
      </button>
      <button type="button" onclick={exportIntuneCsv} disabled={!doc}>Intune CSV</button>
      <button type="button" onclick={exportScorecardsCsv} disabled={!doc}>Scorecards CSV</button>
    </div>
  </div>

  {#if state === "loading"}
    <div class="skeleton card" aria-busy="true">Loading observatory…</div>
  {:else if state === "error"}
    <ErrorRetry title="Could not load insights" message={error} onretry={load} />
  {:else if doc}
    <!-- KPI strip -->
    <div class="kpi-grid" role="group" aria-label="Key metrics">
      <div class="kpi card">
        <div class="kpi-n">{(k.stigs ?? 0).toLocaleString()}</div>
        <div class="kpi-l">STIGs</div>
      </div>
      <div class="kpi card">
        <div class="kpi-n">{(k.rules ?? 0).toLocaleString()}</div>
        <div class="kpi-l">Rules</div>
      </div>
      <div class="kpi card">
        <div class="kpi-n">{(k.vendors ?? 0).toLocaleString()}</div>
        <div class="kpi-l">Vendors</div>
      </div>
      <div class="kpi card">
        <div class="kpi-n">{(k.stigsWithGpo ?? 0)}</div>
        <div class="kpi-l">GPO packages</div>
      </div>
      <div class="kpi card">
        <div class="kpi-n">{(k.rulesWithIntuneMap ?? 0).toLocaleString()}</div>
        <div class="kpi-l">Intune-mapped rules</div>
      </div>
      <div class="kpi card">
        <div class="kpi-n">{(k.rulesWithCis ?? 0)}</div>
        <div class="kpi-l">CIS-mapped rules</div>
      </div>
      <div class="kpi card">
        <div class="kpi-n">{(k.uniqueCcis ?? 0)}</div>
        <div class="kpi-l">Unique CCIs</div>
      </div>
      <div class="kpi card">
        <div class="kpi-n">{k.searchTransferMBGz ?? "—"}</div>
        <div class="kpi-l">Search MB (gzip)</div>
      </div>
    </div>

    <!-- Severity -->
    <div class="card">
      <h2 class="h">Severity mix</h2>
      <div class="sev-track" role="img" aria-label="Severity distribution">
        <div class="sev-seg high" style="flex: {sev.high || 0}" title="High {sev.high}"></div>
        <div class="sev-seg med" style="flex: {sev.medium || 0}" title="Medium {sev.medium}"></div>
        <div class="sev-seg low" style="flex: {sev.low || 0}" title="Low {sev.low}"></div>
        {#if sev.unknown}
          <div class="sev-seg unk" style="flex: {sev.unknown}" title="Unknown {sev.unknown}"></div>
        {/if}
      </div>
      <div class="row legend muted small">
        <span><i class="dot high"></i> High {(sev.high || 0).toLocaleString()} ({share(sev.high, sevTotal)})</span>
        <span><i class="dot med"></i> Medium {(sev.medium || 0).toLocaleString()} ({share(sev.medium, sevTotal)})</span>
        <span><i class="dot low"></i> Low {(sev.low || 0).toLocaleString()} ({share(sev.low, sevTotal)})</span>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs row print-hide" role="tablist" aria-label="Observatory sections">
      {#each [
        ["landscape", "Landscape"],
        ["intune", "Intune surface"],
        ["automation", "Automation"],
        ["crosswalk", "CIS / CCI / ATT&CK"],
        ["threat", "KEV"],
        ["health", "Health & delta"],
      ] as [id, label]}
        <button
          type="button"
          role="tab"
          aria-selected={tab === id}
          class:primary={tab === id}
          onclick={() => (tab = id as typeof tab)}
        >
          {label}
        </button>
      {/each}
    </div>

    {#if tab === "landscape"}
      <div class="grid-2">
        <div class="card">
          <h2 class="h">Top vendors by rule count</h2>
          <ul class="bars">
            {#each (doc.vendors || []).slice(0, 12) as v}
              <li>
                <div class="bar-label">
                  <a href={routes.vendors()}>{v.name}</a>
                  <span class="muted mono">{v.rules.toLocaleString()} · {v.stigs} STIGs</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill" style="width: {barPct(v.rules, maxVendorRules)}"></div>
                </div>
              </li>
            {/each}
          </ul>
        </div>
        <div class="card">
          <h2 class="h">Roles</h2>
          <ul class="bars">
            {#each doc.roles || [] as r}
              <li>
                <div class="bar-label">
                  <span>{r.role}</span>
                  <span class="muted mono">{r.rules.toLocaleString()}</span>
                </div>
                <div class="bar-track">
                  <div
                    class="bar-fill accent2"
                    style="width: {barPct(r.rules, maxRoleRules)}"
                  ></div>
                </div>
              </li>
            {/each}
          </ul>
        </div>
      </div>

      <div class="card">
        <h2 class="h">Family landscape</h2>
        <p class="muted small">
          Tile size ≈ rule count. Green border = GPO package · accent = Intune package · outline
          dash = SHB-related.
        </p>
        <div class="treemap" role="list">
          {#each (doc.landscape || []).slice(0, 48) as cell}
            <div
              class="tile"
              role="listitem"
              class:gpo={cell.hasGpo}
              class:intune={cell.hasIntunePackage}
              class:shb={cell.shbRelated}
              style="flex: {Math.max(1, Math.sqrt(cell.rules))} 1 {Math.max(4.5, Math.sqrt(cell.rules) * 1.1)}rem"
              title="{cell.vendor} / {cell.family}: {cell.rules} rules"
            >
              <div class="tile-v">{cell.vendor}</div>
              <div class="tile-f mono">{cell.family}</div>
              <div class="tile-n muted">{cell.rules}</div>
            </div>
          {/each}
        </div>
      </div>

      <div class="card">
        <h2 class="h">Product scorecards (top STIGs)</h2>
        <div class="table-wrap">
          <table class="data">
            <thead>
              <tr>
                <th>STIG</th>
                <th>Vendor</th>
                <th>Rules</th>
                <th>H / M / L</th>
                <th>Packages</th>
                <th>Intune %</th>
                <th>CIS</th>
                <th>SCAP</th>
              </tr>
            </thead>
            <tbody>
              {#each (doc.scorecards || []).slice(0, 25) as s}
                <tr>
                  <td>
                    {#if s.stigId}
                      <a href={routes.stig(s.stigId)}>{s.name || s.stigId}</a>
                    {:else}
                      {s.name}
                    {/if}
                  </td>
                  <td class="muted">{s.vendor}</td>
                  <td class="mono">{s.ruleCount}</td>
                  <td class="mono small">
                    <span class="sev-h">{s.severity?.high ?? 0}</span>
                    /
                    <span class="sev-m">{s.severity?.medium ?? 0}</span>
                    /
                    <span class="sev-l">{s.severity?.low ?? 0}</span>
                  </td>
                  <td class="small">
                    {#if s.hasGpoPackage}<span class="badge">GPO</span>{/if}
                    {#if s.hasIntunePackage}<span class="badge">Intune pkg</span>{/if}
                    {#if s.shbRelated}<span class="badge">SHB</span>{/if}
                    {#if !s.hasGpoPackage && !s.hasIntunePackage}
                      <span class="muted">—</span>
                    {/if}
                  </td>
                  <td class="mono">
                    {#if s.intuneProduct}
                      <a href={routes.product(s.intuneProduct)}>{s.intuneCoveragePct ?? "—"}%</a>
                    {:else}
                      —
                    {/if}
                  </td>
                  <td class="mono">{s.rulesWithCis ?? 0}</td>
                  <td class="mono">{s.rulesWithScap ?? 0}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {:else if tab === "intune"}
      <p class="muted small">{doc.disclaimers?.intune}</p>
      <div class="prod-grid">
        {#each doc.intuneProducts || [] as p}
          <div class="card prod">
            <div class="row" style="justify-content: space-between">
              <h3 class="h" style="margin:0">
                <a href={routes.product(p.product)}>{p.product}</a>
              </h3>
              <span class="cov mono">{p.coveragePct}%</span>
            </div>
            <p class="muted small" style="margin:0.25rem 0 0.5rem">
              {p.stigName || p.stigId}
            </p>
            <div class="meter" title="{p.mappedRules}/{p.rules} mapped">
              <div class="meter-fill" style="width: {p.coveragePct}%"></div>
            </div>
            <div class="row muted small" style="margin-top:0.4rem">
              <span>{p.mappedRules}/{p.rules} rules</span>
              <span>· {p.settings} OMA-URI settings</span>
            </div>
            <div class="sev-mini row small" style="margin-top:0.5rem">
              <span
                >CAT I: {p.severityCoverage?.high?.mapped ?? 0}/{p.severityCoverage?.high
                  ?.total ?? 0}
                ({p.severityCoverage?.high?.pct ?? 0}%)</span
              >
              <span
                >II: {p.severityCoverage?.medium?.mapped ?? 0}/{p.severityCoverage?.medium
                  ?.total ?? 0}</span
              >
            </div>
            <div class="row small" style="margin-top:0.35rem">
              <span class="badge">conf H {p.confidence?.high ?? 0}</span>
              <span class="badge">M {p.confidence?.medium ?? 0}</span>
              <span class="badge">L {p.confidence?.low ?? 0}</span>
            </div>
            {#if p.unmappedCatI?.length}
              <details style="margin-top:0.65rem">
                <summary class="small">Unmapped CAT I ({p.unmappedCatI.length})</summary>
                <ul class="gap-list">
                  {#each p.unmappedCatI as g}
                    <li>
                      <a class="mono" href={routes.rule(g.id)}>{g.id}</a>
                      <span class="muted small"> — {g.title}</span>
                    </li>
                  {/each}
                </ul>
              </details>
            {/if}
          </div>
        {/each}
      </div>
    {:else if tab === "automation"}
      <div class="grid-2">
        <div class="card">
          <h2 class="h">STIG automation packages</h2>
          <p class="muted small">How many STIGs ship with DISA companion packages.</p>
          <div class="sev-track tall">
            <div
              class="sev-seg both"
              style="flex: {autoStigs.both || 0}"
              title="Both {autoStigs.both}"
            ></div>
            <div
              class="sev-seg gpo"
              style="flex: {autoStigs.gpoPackage || 0}"
              title="GPO {autoStigs.gpoPackage}"
            ></div>
            <div
              class="sev-seg iun"
              style="flex: {autoStigs.intunePackage || 0}"
              title="Intune {autoStigs.intunePackage}"
            ></div>
            <div
              class="sev-seg neither"
              style="flex: {autoStigs.neither || 0}"
              title="Neither {autoStigs.neither}"
            ></div>
          </div>
          <ul class="stat-list">
            <li>
              <strong>{autoStigs.both ?? 0}</strong> both GPO + Intune ({share(
                autoStigs.both,
                autoStigsTotal,
              )})
            </li>
            <li><strong>{autoStigs.gpoPackage ?? 0}</strong> GPO only</li>
            <li><strong>{autoStigs.intunePackage ?? 0}</strong> Intune package only</li>
            <li>
              <strong>{autoStigs.neither ?? 0}</strong> neither ({share(
                autoStigs.neither,
                autoStigsTotal,
              )})
            </li>
            <li><strong>{autoStigs.shb ?? 0}</strong> SHB-related host stack tags</li>
            <li>
              <strong>{autoStigs.manualOrPlatform ?? 0}</strong> manual / platform-native tagged
            </li>
          </ul>
        </div>
        <div class="card">
          <h2 class="h">Rule-level signals</h2>
          <ul class="bars">
            {#each [
              ["withIntuneSuggestion", "Intune map suggestion"],
              ["withScapSignal", "SCAP signal"],
              ["withOval", "OVAL mention"],
              ["withCis", "CIS crosswalk"],
              ["withCkl", "CKL enrichment"],
              ["withDeviation", "Deviation note"],
              ["withAttack", "ATT&CK seed"],
              ["withCve", "CVE in XCCDF"],
              ["withKev", "In KEV"],
            ] as [key, label]}
              <li>
                <div class="bar-label">
                  <span>{label}</span>
                  <span class="muted mono"
                    >{Number(autoRules[key] || 0).toLocaleString()} ({share(
                      Number(autoRules[key] || 0),
                      k.rules || 1,
                    )})</span
                  >
                </div>
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    style="width: {barPct(Number(autoRules[key] || 0), k.rules || 1)}"
                  ></div>
                </div>
              </li>
            {/each}
          </ul>
        </div>
      </div>
    {:else if tab === "crosswalk"}
      <div class="grid-2">
        <div class="card">
          <h2 class="h">CIS crosswalk</h2>
          <p class="muted small">{doc.cis?.disclaimer || doc.disclaimers?.cis}</p>
          <p>
            <strong>{doc.cis?.rulesWithCis ?? 0}</strong> rules mapped ·
            {doc.cis?.mapFiles ?? "—"} map files ·
            <a href={routes.cis()}>Open CIS browser</a>
          </p>
          <h3 class="h small">By product</h3>
          <ul class="bars">
            {#each doc.cis?.byProduct || [] as row}
              <li>
                <div class="bar-label">
                  <span>{row.product}</span>
                  <span class="mono muted">{row.rules}</span>
                </div>
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    style="width: {barPct(row.rules, maxCisProduct)}"
                  ></div>
                </div>
              </li>
            {/each}
          </ul>
        </div>
        <div class="card">
          <h2 class="h">CCI gravity</h2>
          <p class="muted small">
            {doc.cci?.uniqueCcis ?? 0} unique CCIs · {doc.cci?.rulesWithCci?.toLocaleString() ?? "—"}
            rules with ≥1 CCI ·
            <a href={routes.cci()}>CCI browser</a>
          </p>
          <ul class="bars">
            {#each (doc.cci?.top || []).slice(0, 15) as c}
              <li>
                <div class="bar-label">
                  <a class="mono" href={routes.cciId(c.id)}>{c.id}</a>
                  <span class="muted mono">{c.ruleCount.toLocaleString()}</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill accent2" style="width: {barPct(c.ruleCount, maxCci)}"></div>
                </div>
              </li>
            {/each}
          </ul>
        </div>
      </div>
      <div class="card">
        <h2 class="h">ATT&amp;CK technique seeds</h2>
        <p class="muted small">{doc.attack?.disclaimer || doc.disclaimers?.attack}</p>
        <p class="muted small">
          {doc.attack?.rulesWithAttack ?? 0} rules with ≥1 technique seed (keyword-based).
        </p>
        <div class="heat">
          {#each (doc.attack?.techniques || []).slice(0, 24) as t}
            <a
              class="heat-cell"
              href={`https://attack.mitre.org/techniques/${t.id.replace(".", "/")}/`}
              target="_blank"
              rel="noopener"
              style="--w: {0.35 + (t.ruleCount / maxAttack) * 0.65}"
              title="{t.id} {t.name}: {t.ruleCount} rules"
            >
              <span class="mono">{t.id}</span>
              <span class="muted small">{t.ruleCount}</span>
              <span class="heat-name">{t.name}</span>
            </a>
          {/each}
        </div>
      </div>
    {:else if tab === "threat"}
      <div class="card">
        <h2 class="h">CISA KEV observatory</h2>
        <p class="muted small">{doc.kev?.disclaimer || doc.disclaimers?.kev}</p>
        <div class="kpi-grid tight">
          <div class="kpi card inner">
            <div class="kpi-n">{(doc.kev?.catalogCount ?? 0).toLocaleString()}</div>
            <div class="kpi-l">KEV entries</div>
          </div>
          <div class="kpi card inner">
            <div class="kpi-n">{doc.kev?.ransomwareKnown ?? 0}</div>
            <div class="kpi-l">Known ransomware use</div>
          </div>
          <div class="kpi card inner">
            <div class="kpi-n">{doc.kev?.rulesWithKev ?? 0}</div>
            <div class="kpi-l">STIG rules ∩ KEV</div>
          </div>
          <div class="kpi card inner">
            <div class="kpi-n mono small">{doc.kev?.catalogVersion || "—"}</div>
            <div class="kpi-l">Catalog version</div>
          </div>
        </div>
        <p class="muted small">
          Fetched {formatDate(doc.kev?.fetchedAt || "")} ·
          <a href={routes.kev()}>Open KEV browser</a>
        </p>
        <h3 class="h small">Entries by year added</h3>
        <ul class="bars">
          {#each doc.kev?.byYear || [] as y}
            <li>
              <div class="bar-label">
                <span>{y.year}</span>
                <span class="mono muted">{y.count}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" style="width: {barPct(y.count, maxKevYear)}"></div>
              </div>
            </li>
          {/each}
        </ul>
        <h3 class="h small">Top KEV vendors</h3>
        <div class="chip-row">
          {#each (doc.kev?.topVendors || []).slice(0, 16) as v}
            <span class="chip">{v.vendor} <span class="mono">{v.count}</span></span>
          {/each}
        </div>
      </div>
    {:else}
      <div class="grid-2">
        <div class="card">
          <h2 class="h">Library health</h2>
          <ul class="stat-list">
            <li>Built: <span class="mono">{formatDate(doc.health?.builtAt || "")}</span></li>
            <li>Content: <span class="mono">{formatDate(doc.health?.lastUpdated || "")}</span></li>
            <li>Release: <span class="mono">{doc.health?.currentRelease || "—"}</span></li>
            <li>Source: <span class="mono break">{doc.health?.sourceFile || "—"}</span></li>
            <li>Generator: <span class="mono">{doc.health?.generator || "—"}</span></li>
            <li>Parse errors: <strong>{doc.health?.parseErrors ?? 0}</strong></li>
            <li>On-disk data: <strong>{doc.health?.totalMB ?? k.dataTotalMB ?? "—"}</strong> MB · {doc.health?.totalFiles?.toLocaleString() ?? "—"} files</li>
            <li>
              Search transfer: <strong>{k.searchTransferMBGz ?? "—"}</strong> MB gzip ·
              {doc.health?.searchShards ?? "—"} shards
            </li>
          </ul>
        </div>
        <div class="card">
          <h2 class="h">Quarterly delta</h2>
          {#if doc.delta?.available}
            <p class="muted">Multiple releases registered — see <a href={routes.releases()}>Releases</a>.</p>
          {:else}
            <p>
              <strong>Delta theater unlocks after the next DISA library import.</strong>
            </p>
            <p class="muted small">{doc.delta?.note}</p>
          {/if}
          <ul class="stat-list">
            {#each doc.delta?.releases || [] as r}
              <li class="mono">{r.id} {r.label ? `· ${r.label}` : ""}</li>
            {/each}
          </ul>
          <p class="muted small" style="margin-top:0.75rem">
            <a href={routes.releases()}>Releases &amp; changelog</a>
            ·
            <a href={routes.tools()}>Tools</a>
          </p>
        </div>
      </div>
    {/if}

    <p class="muted small disclaimer">
      {doc.disclaimers?.general}
    </p>
  {/if}
</section>

<style>
  .insights .h {
    font-size: 1.05rem;
    margin: 0 0 0.5rem;
  }
  .insights .h.small {
    font-size: 0.92rem;
    margin-top: 0.75rem;
  }
  .small {
    font-size: 0.85rem;
  }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr));
    gap: 0.55rem;
  }
  .kpi-grid.tight {
    margin: 0.75rem 0;
  }
  .kpi {
    text-align: center;
    padding: 0.75rem 0.5rem;
  }
  .kpi.inner {
    background: var(--bg);
  }
  .kpi-n {
    font-size: 1.45rem;
    font-weight: 750;
    letter-spacing: -0.02em;
    color: var(--accent);
    line-height: 1.15;
  }
  .kpi-n.small {
    font-size: 1rem;
  }
  .kpi-l {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .sev-track {
    display: flex;
    height: 1.1rem;
    border-radius: 6px;
    overflow: hidden;
    background: var(--bg);
    border: 1px solid var(--border);
  }
  .sev-track.tall {
    height: 1.5rem;
  }
  .sev-seg.high {
    background: var(--high);
  }
  .sev-seg.med {
    background: var(--medium);
  }
  .sev-seg.low {
    background: var(--low);
  }
  .sev-seg.unk {
    background: var(--info);
  }
  .sev-seg.both {
    background: var(--accent);
  }
  .sev-seg.gpo {
    background: #4a9eff;
  }
  .sev-seg.iun {
    background: #c084fc;
  }
  .sev-seg.neither {
    background: #3a4a40;
  }
  .legend {
    margin-top: 0.5rem;
    gap: 1rem;
  }
  .dot {
    display: inline-block;
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 50%;
    margin-right: 0.25rem;
  }
  .dot.high {
    background: var(--high);
  }
  .dot.med {
    background: var(--medium);
  }
  .dot.low {
    background: var(--low);
  }
  .tabs {
    gap: 0.4rem;
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }
  @media (max-width: 800px) {
    .grid-2 {
      grid-template-columns: 1fr;
    }
  }
  .bars {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .bar-label {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    font-size: 0.88rem;
  }
  .bar-track {
    height: 0.45rem;
    background: var(--bg);
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid var(--border);
  }
  .bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-dim), var(--accent));
    border-radius: 4px;
    min-width: 2px;
  }
  .bar-fill.accent2 {
    background: linear-gradient(90deg, #2a6e9e, #5ab0e6);
  }
  .treemap {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: 0.5rem;
  }
  .tile {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.35rem 0.45rem;
    min-width: 5rem;
    min-height: 3.2rem;
    overflow: hidden;
  }
  .tile.gpo {
    border-color: #4a9eff;
  }
  .tile.intune {
    border-color: var(--accent);
  }
  .tile.shb {
    border-style: dashed;
  }
  .tile-v {
    font-size: 0.72rem;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .tile-f {
    font-size: 0.78rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .tile-n {
    font-size: 0.75rem;
  }
  .table-wrap {
    overflow-x: auto;
  }
  table.data {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
  }
  table.data th,
  table.data td {
    text-align: left;
    padding: 0.4rem 0.5rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }
  table.data th {
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .sev-h {
    color: var(--high);
  }
  .sev-m {
    color: var(--medium);
  }
  .sev-l {
    color: var(--low);
  }
  .badge {
    display: inline-block;
    font-size: 0.72rem;
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
    background: var(--chip);
    border: 1px solid var(--border);
    margin-right: 0.2rem;
  }
  .prod-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr));
    gap: 0.65rem;
  }
  .cov {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--accent);
  }
  .meter {
    height: 0.55rem;
    background: var(--bg);
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid var(--border);
  }
  .meter-fill {
    height: 100%;
    background: var(--accent);
  }
  .gap-list {
    margin: 0.35rem 0 0;
    padding-left: 1.1rem;
    font-size: 0.82rem;
  }
  .stat-list {
    margin: 0.5rem 0 0;
    padding-left: 1.1rem;
    line-height: 1.65;
  }
  .heat {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.5rem;
  }
  .heat-cell {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    padding: 0.4rem 0.5rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: color-mix(in srgb, var(--accent) calc(var(--w) * 35%), var(--bg-elevated));
    text-decoration: none;
    color: inherit;
    min-width: 6.5rem;
    max-width: 11rem;
  }
  .heat-cell:hover {
    border-color: var(--accent);
    text-decoration: none;
  }
  .heat-name {
    font-size: 0.72rem;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-top: 0.35rem;
  }
  .chip {
    font-size: 0.8rem;
    padding: 0.2rem 0.45rem;
    border-radius: 999px;
    background: var(--chip);
    border: 1px solid var(--border);
  }
  .disclaimer {
    margin-top: 0.5rem;
  }
  .break {
    word-break: break-all;
  }
  .mono {
    font-family: var(--mono);
  }
</style>
