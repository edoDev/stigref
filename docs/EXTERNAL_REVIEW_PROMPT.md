# External design review prompt (Claude Opus / Sonnet / Fable)

Copy everything below the line into a **fresh** conversation with the reviewer model. Attach or paste `docs/DESIGN.md` and `README.md` if the tool cannot read the repo.

---

## Prompt (copy from here)

You are a senior product engineer reviewing a **pre-implementation design** for a new open-source project. Be fair, specific, and adversarial where needed. Do **not** rewrite the whole design; return a structured review.

### Context

The project is **stigref**: a **static**, GitHub Pages–hosted **STIG/SRG and control reference** site with:

- Fast lightweight frontend
- Robust client-side search
- Deep links to STIGs, rules, and controls
- One-click clean copy/paste (IDs, check/fix, citation blocks)
- Quarterly (or CI) ingest of public DISA `U_` library ZIPs → generated JSON
- Explicit non-goals: no assessment workflow, no assets/collections, no auth, no CUI content

It is intentionally **not** STIG Manager (NUWCDIVNPT)—that product manages evaluations. stigref is “look up / link / copy.”

Prior art failures to avoid: rmfdb-style SPA that depends on a dead API and infinite loading spinners on error; assuming browser can CORS-fetch DISA ZIPs (it cannot).

### Materials

Review the attached/pasted:

- Product README
- DESIGN.md (problem, IA, data layout, phases, risks)
- ARCHITECTURE.md if provided

### Review criteria

Score each 1–5 (5 = excellent) and justify in 2–4 sentences:

1. **Problem–solution fit**
2. **Differentiation clarity** (vs STIG Manager / STIG Viewer / cyber.mil)
3. **Technical feasibility** on GitHub Pages only
4. **Search architecture** (index vs detail split, scale of full library)
5. **Deep linking & ID stability**
6. **Copy/paste UX design**
7. **Data pipeline & maintainer burden**
8. **Scope control / non-goals**
9. **Risks & mitigations completeness**
10. **Phasing / MVP cut**

### Required outputs

1. **Executive verdict:** Approve / Approve with changes / Major rethink — one paragraph.
2. **Score table** for the 10 criteria + **overall**.
3. **Top 5 strengths.**
4. **Top 5 issues or gaps** (ordered by severity), each with a concrete recommendation.
5. **Data-size reality check:** Is the proposed JSON/index strategy credible for a full public STIG library (~hundreds of STIGs, tens of thousands of rules)? What would you change?
6. **ID scheme critique:** Will rule/STIG IDs stay stable across quarterly rebuilds and mid-cycle individual STIG updates?
7. **What to cut from v1** if the team is one maintainer + AI pair programming.
8. **What to add to v1** if missing for a usable product.
9. **Security/compliance notes** for redistributing transformed public STIG text on GitHub Pages.
10. **Final checklist** of decisions the owner must make before coding.

### Rules for the reviewer

- Prefer evidence and engineering judgment over generic best-practice fluff.
- Call out over-scoping and under-scoping equally.
- If you disagree with Svelte vs React, say so with rationale—but do not derail the review on framework fashion.
- Assume DISA provides ZIP/XCCDF only, no official public JSON API, no CORS for SPA fetch.
- Do not implement code; design review only.

### Optional fairness note

The design was drafted with assistance from Grok (xAI) in a planning conversation that also reverse-engineered rmfdb and surveyed cyber.mil download mechanics. Review the **design quality**, not the authoring tool.

---

## After you get results

Paste the review back into the stigref design thread so gaps can be merged into DESIGN.md before Phase 1 implementation.
