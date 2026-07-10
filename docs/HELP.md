# stigref user guide

**What stigref is:** a fast, free, **static** browser for public DISA STIGs/SRGs—search, deep-link, copy text, and see Intune/GPO/KEV context.  
**What it is not:** an assessment tool (no assets, scores, or .ckl workflow). For that, use [STIG Manager](https://github.com/NUWCDIVNPT/stig-manager) or STIG Viewer.

**Live site:** [https://edodev.github.io/stigref/](https://edodev.github.io/stigref/)  
**Source:** [github.com/edoDev/stigref](https://github.com/edoDev/stigref)

---

## Quick orientation

| Nav item | Purpose |
|----------|---------|
| **Search** | Full-text search + filters; shareable URLs |
| **STIGs** | Catalog of all STIGs with automation filters |
| **Products** | Quick-link hubs (Win11, Edge, Defender, …) + Intune packs |
| **KEV** | Browse/search the CISA Known Exploited Vulnerabilities catalog |
| **Saved** | Bookmarks stored in *this browser only* |
| **About** | Catalog metadata, themes, disclaimers |

**Theme:** use the header **Theme** control (Carbon Green is the default). Preference is saved in the browser.

**Content date:** header shows *Content updated …* from the last STIG library build (not the site deploy time).

---

## Use case 1 — Find a rule by ID and share the link

**Who:** ISSO, admin, ticket author  
**Goal:** Open `SV-253284…` and paste a stable URL into a ticket.

1. Go to **Search**.
2. Type the rule ID (e.g. `SV-253284` or full `SV-253284r958928_rule`).
3. Open the matching **rule** result.
4. Copy the browser address bar, or use **Citation** / **Markdown** under copy packs.
5. Share the URL—anyone with the link opens the same rule (after the site is published).

**Tip:** Partial IDs work. Severity and vendor filters refine noisy searches.

---

## Use case 2 — Search by keyword and filter the catalog

**Who:** Engineer looking for “BitLocker”, “SMBv1”, “telemetry”  
**Goal:** Narrow ~20k rules/STIGs quickly.

1. On **Search**, enter a keyword (e.g. `bitlocker`).
2. Optionally set filters:
   - **Type:** Rules or STIGs  
   - **Severity:** high / medium / low  
   - **Vendor:** e.g. Microsoft  
   - **Has Intune map** / **Has CVE** / **In CISA KEV**
3. Open a result. The URL updates (e.g. `?q=bitlocker&severity=high`) so you can share the *search*, not only a single rule.

**Tip:** Clear filters with **Clear** when results look empty.

---

## Use case 3 — Jump to a common product (Windows 11, Edge, …)

**Who:** Desktop / Intune admin  
**Goal:** Start from a known product, not free text.

1. On **Search**, use **Quick links** (coverage % shows Intune map completeness).  
   Or open **Products** for the full list.
2. Click **Windows 11** (or Edge, Defender AV, Server 2022, …).
3. On the **product hub**:
   - See Intune map coverage bar  
   - Open the full STIG  
   - **Copy settings CSV** / **Copy pack README** for Intune handoff  
   - Open raw export JSON if needed  
4. From the STIG page, drill into individual rules.

---

## Use case 4 — Copy check/fix text cleanly for a change ticket

**Who:** Sysadmin documenting a fix  
**Goal:** Paste plain text without HTML junk.

1. Open the rule.
2. Use the copy pack buttons:
   | Button | Copies |
   |--------|--------|
   | **Copy ID** | Rule ID only |
   | **Citation** | ID, title, severity, STIG, link |
   | **Markdown** | Formatted block for GitHub/GitLab |
   | **Check** | Check content only |
   | **Fix** | Fix text only |
   | **OMA-URIs** | Tab-separated Intune OMA rows (when mapped) |
   | **Intune JSON** | Suggestion objects as JSON |
3. Paste into the ticket or runbook.

---

## Use case 5 — Apply a setting in Microsoft Intune (with DISA context)

**Who:** Intune administrator  
**Goal:** See what DISA suggests for GPO vs Intune and how to deploy.

1. Open a Windows/browser/Defender product rule (quick-link products have the richest data).
2. Scroll to **DISA package mapping** (when present):
   - **GPO:** which DISA GPO implements the setting  
   - **Intune:** Settings Catalog / DSC / script note from DISA’s checklist  
   - **Outside GPO scope** = not handled by DISA’s GPO baseline  
   - **Not native to Intune** = deviations workbook (may need DSC/script)  
3. Open **Intune / CSP suggestions**:
   - Expand **How to apply in Intune**  
   - Note **kind** (native vs admx-backed) and **confidence**  
   - Use **Learn / usage** for the official CSP page  
   - Copy OMA-URI and value  
4. On the **product hub**, copy the full **settings CSV** for bulk review.
5. Pilot on a test group; verify with the STIG **Check** text—not only the suggestion.

**Disclaimer:** Suggestions and package notes are **assistive**. Validate against your org policy and current Microsoft docs.

---

## Use case 6 — Identify manual / non-GPO / non-Intune STIGs

**Who:** Architect scoping automation work  
**Goal:** See what cannot be bulk-applied via DISA GPO/Intune packages.

1. Open **STIGs**.
2. Use **Automation** filter or chips:
   - **Has DISA GPO package**  
   - **Has DISA Intune package**  
   - **No DISA GPO/Intune package**  
   - **Manual / platform-native** (network, DB, appliance, etc.)  
   - **SHB-related** (typical Windows host stack)  
3. Open a STIG → **Automation & packages** card for details.
4. On individual rules, check-style badges (**manual**, **policy-amenable**) appear when the check text is obvious.

**Note:** “Manual / platform-native” means no matching DISA host GPO/Intune product package—not that the product cannot be hardened another way.

---

## Use case 7 — Secure Host Baseline (SHB)–style host stack

**Who:** Windows baselining team  
**Goal:** Focus on STIGs that usually form a hardened workstation host set.

1. **STIGs** → filter **SHB-related**.  
2. Expect items such as Windows 10/11, Edge, Chrome, Defender AV/FW, Office/M365, Reader (exact set depends on the library quarter).  
3. Use **Products** hubs for Intune/GPO package notes on those STIGs.

**Note:** This is a **discoverability tag**, not an official DoD SHB product matrix.

---

## Use case 8 — Browse CISA KEV (even when STIGs rarely cite CVEs)

**Who:** Vulnerability / cyber ops  
**Goal:** Search Known Exploited Vulnerabilities without leaving stigref.

1. Open **KEV**.
2. Search by CVE, vendor, product, or description (e.g. `Chrome`, `Exchange`).
3. Filter:
   - **Vendor**  
   - **Known ransomware use**  
   - **Linked to STIG rules** (when this library’s STIGs cite that CVE)  
4. Open **NVD** or **CISA KEV** for authoritative detail.
5. If **STIG rule(s)** links appear, jump into stigref’s rule page.

**Tip:** Most STIG rules do not list CVEs; KEV is still useful as a standalone catalog snapshot updated at build time.

---

## Use case 9 — Threat context on a rule (CVE / KEV)

**Who:** Risk owner reviewing a finding  
**Goal:** See public CVE/KEV context next to the STIG text.

1. Open the rule.
2. If present, **Threat context** shows CVE chips (red **KEV** when in CISA’s catalog).
3. Click a CVE → NVD.
4. Read the disclaimer: this is **not** a scan result and **not** a finding determination.

Search filters **Has CVE** / **In CISA KEV** find rules that carry those tags in the current build.

---

## Use case 10 — Bookmark rules for a project (local only)

**Who:** Engineer working a remediation sprint  
**Goal:** Keep a short list without accounts.

1. On a rule or STIG page, click **☆ Save** (becomes **★ Saved**).
2. Open **Saved** in the nav to revisit.
3. **Remove** when done.

Bookmarks live in **localStorage** on this browser only—they are not synced or backed up by stigref.

---

## Use case 11 — Print or archive a rule for audit evidence

**Who:** Auditor / documentation  
**Goal:** Clean paper or PDF capture.

1. Open the rule.
2. Use the browser **Print** dialog (Ctrl/Cmd+P).  
3. Prefer **Citation** or **Markdown** in the ticket if digital evidence is enough.

*(Print-optimized CSS may improve over time; content is already plain and readable.)*

---

## Use case 12 — Quarterly content update (maintainer)

**Who:** stigref maintainer  
**Goal:** Refresh STIGs + packages + KEV after DISA’s quarter.

1. Download into `raw/` (not committed):
   - `U_SRG-STIG_Library_<Quarter>.zip`
   - `U_STIG_GPO_Package_<Quarter>.zip` (recommended)
   - `U_Intune_Policy_Package_<Quarter>.zip` (recommended)
2. Build:
   ```powershell
   cd scripts
   .\.venv\Scripts\Activate.ps1
   python -m stigref_build -i ..\raw\U_SRG-STIG_Library_….zip -o ..\data
   ```
3. Run tests: `pytest -q`
4. Commit updated `data/` (and code if needed); push `main` → GitHub Pages deploys.

See also: [PACKAGES.md](./PACKAGES.md), [INTUNE_CSP.md](./INTUNE_CSP.md).

---

## Trust and limitations

| Topic | Guidance |
|-------|----------|
| **Accuracy** | STIG check text is the requirement; Intune/GPO notes assist implementation |
| **CUI** | Public `U_` content only |
| **Intune multi-option** | Not always 1:1 with GPO/ADMX—read confidence and Learn links |
| **KEV/CVE** | Public context; rare STIG↔KEV overlap is normal |
| **SHB tag** | Informal host-stack grouping |
| **Offline packages** | Raw DISA zips stay on the maintainer machine; the site serves derived JSON |

---

## Keyboard / power tips

- Paste shareable search URLs into chat for the same filter state  
- Use **Markdown** copy for PR descriptions  
- Product hub CSV → Excel for bulk Intune review  
- Filter **manual/platform** on STIGs when scoping automation ROI  

---

## Getting help / contributing

- Issues & source: [github.com/edoDev/stigref](https://github.com/edoDev/stigref)  
- Intune map contributions: `scripts/stigref_build/intune_maps/` (see README there)  
- Product backlog: [BACKLOG.md](./BACKLOG.md)  
