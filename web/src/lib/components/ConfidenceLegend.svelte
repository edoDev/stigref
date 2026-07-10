<script lang="ts">
  interface Props {
    compact?: boolean;
  }
  let { compact = false }: Props = $props();
</script>

<details class="legend" class:compact>
  <summary>Confidence &amp; source legend</summary>
  <ul>
    <li>
      <strong>high</strong> — direct curated map or authoritative catalog match (e.g. CVE ∈ CISA
      KEV).
    </li>
    <li>
      <strong>medium</strong> — strong heuristic (registry/CSP path match) still needs human review.
    </li>
    <li>
      <strong>low</strong> — keyword / weak match; treat as a starting point only.
    </li>
    <li>
      <strong>Threat / Intune panels</strong> are public context and operator aids — not STIG findings
      and not a vulnerability scan result.
    </li>
  </ul>
</details>

<style>
  .legend {
    font-size: 0.85rem;
    color: var(--text-muted);
  }
  .legend.compact {
    margin: 0;
  }
  .legend summary {
    cursor: pointer;
    color: var(--text-muted);
    font-weight: 600;
  }
  .legend ul {
    margin: 0.4rem 0 0;
    padding-left: 1.15rem;
  }
  .legend li {
    margin: 0.2rem 0;
  }
  .legend strong {
    color: var(--text);
  }
</style>
