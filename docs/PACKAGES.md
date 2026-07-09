# DISA companion packages (GPO + Intune)

## What you added

| File | Role |
|------|------|
| `raw/U_STIG_GPO_Package_April_2026.zip` | **Yes — highly useful.** ADMX templates, GPO backups, GP reports, checklists for Windows 10/11/Server, Edge, Chrome, Firefox, IE11, Defender AV/FW, Office/M365, Adobe. |
| `raw/U_Intune_Policy_Package_April_2026.zip` | **Yes — highly useful.** Importable Intune JSON: Settings Catalog, Administrative Templates, Custom profiles, scripts (Win11/10, Edge, Chrome, Defender, Firewall, M365, Adobe, …). |

## How stigref uses them

During each quarterly `stigref_build`:

1. Detect packages under `raw/` matching:
   - `U_STIG_GPO_Package_*.zip`
   - `U_Intune_Policy_Package_*.zip`
2. Index product folders / policy JSON names.
3. Match STIGs by title keywords.
4. Annotate each STIG with `automation` + tags:
   - `has-gpo-package` / `no-gpo-package`
   - `has-intune-package` / `no-intune-package`
   - `manual-or-platform-native` (no package + non-host class)
   - `shb-related` (Secure Host Baseline–style host stack)
5. Write `data/packages/index.json` for UI/docs.

**Raw packages are not committed** (large, redistributable from cyber.mil). Only derived indexes/tags are published.

## Enrichment value (future)

| Source | Future use |
|--------|------------|
| GPO `gpreport.xml` / checklist CKL | Map STIG rule IDs → GPO settings (stronger than heuristics) |
| Intune Settings Catalog JSON | Real Graph setting definitions → better OMA-URI / Settings Catalog names |
| `Intune STIG Deviations and Unsupported Settings.xlsx` | Explicit “not supported in Intune” rule flags |
| ADMX templates | Chrome/Edge/Office ADMX-backed map expansion |

## SHB note

**Secure Host Baseline (SHB)** is a DoD deployment framework (historically Windows 10 host images + layered STIGs/GPOs). stigref tags **SHB-related** STIGs that typically form a hardened **Windows host** stack (OS + browser + Defender + firewall + Office/Reader). This is **not** an official SHB product matrix.

## Quarterly ops

```
raw/
  U_SRG-STIG_Library_<Quarter>.zip
  U_STIG_GPO_Package_<Quarter>.zip      # optional but recommended
  U_Intune_Policy_Package_<Quarter>.zip # optional but recommended

python -m stigref_build -i raw/U_SRG-STIG_Library_….zip -o ../data
```

If GPO/Intune zips are missing, build still succeeds; STIGs simply get `no-*-package` tags.
