<script lang="ts">
  import { routes } from "../paths";

  /** Lightweight NIST 800-53 fixtures — not a full control catalog (B-028) */
  const FIXTURES = [
    {
      id: "AC-2",
      title: "Account Management",
      note: "Maps commonly to Windows account / privileged user STIGs. Use CCI browser for evidence links.",
    },
    {
      id: "AC-3",
      title: "Access Enforcement",
      note: "Least privilege, UAC, rights assignment style STIG rules.",
    },
    {
      id: "AU-2",
      title: "Event Logging",
      note: "Audit policy and event log size STIGs.",
    },
    {
      id: "CM-6",
      title: "Configuration Settings",
      note: "Bulk of STIG technical settings; start from product hubs.",
    },
    {
      id: "IA-2",
      title: "Identification and Authentication",
      note: "Password, smart card, MFA-related STIGs.",
    },
    {
      id: "SC-8",
      title: "Transmission Confidentiality and Integrity",
      note: "TLS / SMB / protocol hardening STIGs.",
    },
    {
      id: "SI-2",
      title: "Flaw Remediation",
      note: "Patching; pair with KEV browser for exploited vulns.",
    },
    {
      id: "SI-3",
      title: "Malicious Code Protection",
      note: "Defender Antivirus STIG / product hub.",
    },
  ];
</script>

<section class="stack">
  <div>
    <h1>NIST 800-53 (fixtures)</h1>
    <p class="muted">
      Lightweight navigation aids only (B-028) — not an authoritative SP 800-53 catalog or full
      control→CCI matrix. Prefer CCI browser for concrete rule links.
    </p>
  </div>

  <ul class="list card">
    {#each FIXTURES as c}
      <li class="item">
        <div class="row">
          <strong class="mono">{c.id}</strong>
          <span>{c.title}</span>
        </div>
        <p class="muted small">{c.note}</p>
        <a href={`${routes.home()}?q=${encodeURIComponent(c.id)}`}>Search “{c.id}”</a>
        ·
        <a href={routes.cci()}>CCI browser</a>
      </li>
    {/each}
  </ul>
</section>

<style>
  .item {
    padding: 0.75rem;
    border-bottom: 1px solid var(--border);
  }
  .item:last-child {
    border-bottom: none;
  }
  .small {
    font-size: 0.88rem;
    margin: 0.35rem 0;
  }
</style>
