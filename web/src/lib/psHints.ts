/** “Verify in Windows” PowerShell hint templates — B-020 */

export function powershellHints(rule: {
  title?: string;
  check?: string;
  full_rule_id?: string;
}): Array<{ label: string; script: string }> {
  const title = (rule.title || "").toLowerCase();
  const check = (rule.check || "").toLowerCase();
  const blob = `${title} ${check}`;
  const out: Array<{ label: string; script: string }> = [];

  if (/registry|hklm|hkcu|hkey_/.test(blob)) {
    out.push({
      label: "Read a registry value",
      script: `# Replace path/name with values from the STIG check text
Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\...' -Name 'ValueName' -ErrorAction SilentlyContinue`,
    });
  }
  if (/service|running|stopped/.test(blob)) {
    out.push({
      label: "Check service status",
      script: `Get-Service -Name 'ServiceName' | Format-List Name, Status, StartType`,
    });
  }
  if (/firewall/.test(blob)) {
    out.push({
      label: "Firewall profile state",
      script: `Get-NetFirewallProfile | Select-Object Name, Enabled`,
    });
  }
  if (/defender|antivirus|mpcomputer/.test(blob)) {
    out.push({
      label: "Defender preferences",
      script: `Get-MpComputerStatus | Select-Object AMServiceEnabled, AntispywareEnabled, RealTimeProtectionEnabled
Get-MpPreference | Select-Object DisableRealtimeMonitoring, PUAProtection`,
    });
  }
  if (/bitlocker|encryption/.test(blob)) {
    out.push({
      label: "BitLocker volume status",
      script: `Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus, ProtectionStatus, EncryptionPercentage`,
    });
  }
  if (/audit|event log/.test(blob)) {
    out.push({
      label: "Audit policy (advanced)",
      script: `auditpol /get /category:*`,
    });
  }
  if (/smb|lanman/.test(blob)) {
    out.push({
      label: "SMB server configuration",
      script: `Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol`,
    });
  }
  if (/uac|elevation|user account control/.test(blob)) {
    out.push({
      label: "UAC registry settings",
      script: `Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' |
  Select-Object EnableLUA, ConsentPromptBehaviorAdmin, PromptOnSecureDesktop`,
    });
  }

  // Always offer a generic template
  out.push({
    label: "Generic: restate STIG check locally",
    script: `# ${rule.full_rule_id || "rule"}
# Use the STIG Check text as the source of truth.
# Example pattern: compare a setting, then document evidence for your assessment tool.
Write-Output 'Validate against STIG check text — this is an operator aid only.'`,
  });

  return out.slice(0, 5);
}
