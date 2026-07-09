# stigref build pipeline (Phase 1)

Convert DISA XCCDF / STIG ZIPs / SRG-STIG library ZIPs into the static `data/` tree consumed by the future web UI.

## Setup

```powershell
cd scripts
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Build from the sample fixture

```powershell
cd scripts
python -m stigref_build --input testdata/sample_stig-xccdf.xml --out ..\data
```

## Build from a real DISA package

```powershell
# Download a public U_ library or individual STIG zip into ../raw/
python -m stigref_build --input ..\raw\U_SRG-STIG_Library_April_2026.zip --out ..\data -v
```

## Tests

```powershell
cd scripts
pytest -q
```

## Output layout

```
data/
  meta.json
  stigs/index.json
  stigs/by-id/{stigId}.json
  rules/by-id/{ruleId}.json
  search/documents.json
```
