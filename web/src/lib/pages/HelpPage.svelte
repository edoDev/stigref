<script lang="ts">
  import { routes } from "../paths";
</script>

<section class="stack help">
  <div>
    <h1>Help &amp; walkthroughs</h1>
    <p class="muted">
      Common ways to use stigref. Full maintainer docs also live in the
      <a href="https://github.com/edoDev/stigref/blob/main/docs/HELP.md" target="_blank" rel="noopener"
        >repo HELP.md</a
      >.
    </p>
  </div>

  <div class="card stack">
    <h2>What this site is</h2>
    <p style="margin:0">
      A <strong>static</strong> browser for public DISA STIGs: search, deep links, clean copy, Intune/GPO
      package notes, and public CVE/KEV context. It does <strong>not</strong> track assessment status on
      assets—use STIG Manager or STIG Viewer for formal checklists.
    </p>
    <p class="muted" style="margin:0">
      Header shows the active library <em>release</em> and <em>Content updated</em> from the STIG build.
      Appearance is fixed to Carbon Green. Keyboard: <kbd>/</kbd> focus search, <kbd>?</kbd> this help,
      <kbd>g</kbd> then <kbd>s</kbd>/<kbd>k</kbd>/<kbd>p</kbd>/<kbd>h</kbd> for STIG/KEV/Products/Home.
    </p>
  </div>

  <div class="card stack">
    <h2>1. Find a rule by ID and share the link</h2>
    <ol>
      <li>Open <a href={routes.home()}>Search</a>.</li>
      <li>Type a rule ID (e.g. <span class="mono">SV-253284</span>).</li>
      <li>Open the rule result.</li>
      <li>Share the browser URL, or use <strong>Citation</strong> / <strong>Markdown</strong> copy packs.</li>
    </ol>
  </div>

  <div class="card stack">
    <h2>2. Keyword search with filters</h2>
    <ol>
      <li>Search for a term such as <span class="mono">bitlocker</span> or <span class="mono">smb</span>.</li>
      <li>
        Narrow with Type, Severity, Vendor, and checkboxes: Has Intune map, Has CVE, In CISA KEV.
      </li>
      <li>Copy the address bar—the query string is shareable (e.g. <span class="mono">?q=bitlocker&amp;severity=high</span>).</li>
    </ol>
  </div>

  <div class="card stack">
    <h2>3. Start from a product (Windows 11, Edge, Defender…)</h2>
    <ol>
      <li>Use <strong>Quick links</strong> on Search (shows Intune map coverage %), or open <a href={routes.products()}>Products</a>.</li>
      <li>Open a product hub for coverage, STIG link, and Intune export tools.</li>
      <li><strong>Copy settings CSV</strong> / README for handoff to an Intune admin.</li>
    </ol>
  </div>

  <div class="card stack">
    <h2>4. Copy check/fix for a ticket</h2>
    <ol>
      <li>Open any rule.</li>
      <li>
        Use copy packs: ID, Citation, Markdown, Check, Fix, OMA-URIs (when mapped), Intune JSON.
      </li>
      <li>Paste into the change ticket or runbook—plain text, no STIG Viewer formatting noise.</li>
    </ol>
  </div>

  <div class="card stack">
    <h2>5. Implement a setting in Intune (with DISA package notes)</h2>
    <ol>
      <li>Open a Windows / browser / Defender rule from a quick-link product.</li>
      <li>
        Read <strong>DISA package mapping</strong>: which GPO and Intune profile DISA associates, or
        “outside GPO scope” / “not native to Intune”.
      </li>
      <li>
        Open <strong>Intune / CSP suggestions</strong> → expand <em>How to apply in Intune</em>.
      </li>
      <li>Copy OMA-URI and value; follow the Learn link for official CSP usage.</li>
      <li>Pilot, then verify with the STIG <strong>Check</strong> text—not only the suggestion.</li>
    </ol>
    <p class="muted" style="margin:0">
      Suggestions are assistive. Multi-option rows mean GPO/ADMX and native CSP are not always 1:1.
    </p>
  </div>

  <div class="card stack">
    <h2>6. Find manual or non-package STIGs</h2>
    <ol>
      <li>Open <a href={routes.stigs()}>STIGs</a>.</li>
      <li>
        Filter Automation: GPO package, Intune package, No DISA package, Manual/platform-native, or
        SHB-related.
      </li>
      <li>Open a STIG for the <strong>Automation &amp; packages</strong> card.</li>
    </ol>
    <p class="muted" style="margin:0">
      Manual/platform-native means no matching DISA host GPO/Intune product package (e.g. many network
      or database STIGs)—not that hardening is impossible another way.
    </p>
  </div>

  <div class="card stack">
    <h2>7. SHB-style Windows host stack</h2>
    <ol>
      <li>On STIGs, chip or filter <strong>SHB-related</strong>.</li>
      <li>
        Typical set: Windows 10/11, Edge/Chrome, Defender AV/FW, Office/M365, Reader (varies by quarter).
      </li>
      <li>Use product hubs for package and Intune coverage on those STIGs.</li>
    </ol>
    <p class="muted" style="margin:0">
      SHB tag is for discoverability—not an official Secure Host Baseline product list.
    </p>
  </div>

  <div class="card stack">
    <h2>8. Library Observatory (metrics)</h2>
    <ol>
      <li>Open <a href={routes.insights()}>Insights</a>.</li>
      <li>
        Review KPI strip, severity mix, vendor landscape, Intune coverage scorecards, automation
        package mix, CIS/CCI/ATT&amp;CK, and KEV catalog stats.
      </li>
      <li>Use <strong>Copy board pack</strong> for a Markdown brief or export CSVs for planning.</li>
    </ol>
    <p class="muted" style="margin:0">
      Metrics are precomputed at build time from public STIG data and curated maps—not a compliance
      score or vulnerability assessment. Quarterly delta charts unlock after a second library import.
    </p>
  </div>

  <div class="card stack">
    <h2>9. Browse CISA KEV</h2>
    <ol>
      <li>Open <a href={routes.kev()}>KEV</a>.</li>
      <li>Search CVE, vendor, or product; filter ransomware or “linked to STIG rules”.</li>
      <li>Use NVD / CISA links for authoritative detail.</li>
    </ol>
    <p class="muted" style="margin:0">
      Most STIG rules do not cite CVEs; KEV is still a full searchable catalog snapshot from the last
      data build.
    </p>
  </div>

  <div class="card stack">
    <h2>10. Threat context on a rule</h2>
    <ol>
      <li>Open a rule that has CVE identifiers.</li>
      <li><strong>Threat context</strong> shows CVE chips; KEV is highlighted when applicable.</li>
      <li>Treat this as public context only—not a vulnerability scan or finding status.</li>
    </ol>
  </div>

  <div class="card stack">
    <h2>11. Bookmark work for a sprint</h2>
    <ol>
      <li>On a rule or STIG, click <strong>☆ Save</strong>.</li>
      <li>Reopen from <a href={routes.saved()}>Saved</a>.</li>
      <li>Bookmarks stay in this browser only (localStorage)—not synced to an account.</li>
    </ol>
  </div>

  <div class="card stack">
    <h2>Maintainer: quarterly refresh</h2>
    <ol>
      <li>
        Place under <span class="mono">raw/</span>: STIG library zip, optional GPO package, optional
        Intune package.
      </li>
      <li>
        Run <span class="mono">python -m stigref_build -i … -o ../data</span> then tests and push.
      </li>
    </ol>
    <p style="margin:0">
      Details:
      <a href="https://github.com/edoDev/stigref/blob/main/docs/PACKAGES.md" target="_blank" rel="noopener"
        >PACKAGES.md</a
      >,
      <a href="https://github.com/edoDev/stigref/blob/main/docs/INTUNE_CSP.md" target="_blank" rel="noopener"
        >INTUNE_CSP.md</a
      >.
    </p>
  </div>

  <div class="card stack">
    <h2>Trust checklist</h2>
    <ul>
      <li>STIG <strong>check text</strong> is the requirement.</li>
      <li>Intune/GPO package notes assist implementation; validate before production.</li>
      <li>Public <span class="mono">U_</span> content only—no CUI.</li>
      <li>CVE/KEV are public context, not scan results.</li>
    </ul>
  </div>
</section>

<style>
  .help h2 {
    margin: 0;
    font-size: 1.05rem;
  }
  .help ol,
  .help ul {
    margin: 0;
    padding-left: 1.2rem;
  }
  .help li {
    margin: 0.35rem 0;
  }
</style>
