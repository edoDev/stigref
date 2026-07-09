# Using Grok (Build) effectively on stigref

## Session strategy

| Phase | How to use Grok |
|-------|------------------|
| Design (now) | One long thread for product decisions; freeze DESIGN.md before code |
| Pipeline | Dedicated session: “implement `scripts/build_data.py` only, with fixtures” |
| UI shell | Dedicated session: Vite app, routes, copy components, no full data |
| Search | Dedicated session: MiniSearch worker + index contract tests |
| Integration | Session: wire data shapes, empty/error states, Pages deploy |
| Review | Use `/review` or paste external Claude review findings to fix |

**Prefer vertical slices** (“one STIG sample end-to-end”) over “build entire app in one prompt.”

## Prompting tips that work well

1. **Point at files** — “Read `docs/DESIGN.md` §7 and implement only the search document schema + writer.”
2. **State invariants** — “No Flask, no API routes, no infinite spinner, public `U_` only.”
3. **Give acceptance checks** — “`python -m pytest`” / “`npm run build`” / “curl Pages 404 fallback.”
4. **Ask for plans on multi-file work** — then approve before a large apply.
5. **Separate research from edit** — “Do not modify files; list XCCDF fields we must capture.”
6. **Paste failures** — full traceback + command; avoid “it doesn’t work.”
7. **Budget context** — don’t paste entire library JSON into chat; use sample fixtures under `scripts/testdata/`.

## What to avoid

- “Rebuild rmfdb” (carries bad patterns)
- Mixing assessment features into v1 prompts
- Asking to scrape cyber.mil Salesforce UI when `dl.dod.cyber.mil/.../stigs/zip/` directory index is enough
- Generating full production data inside the agent chat

## Suggested milestone prompts (after approval)

```text
Phase 1a: Create scripts/ with parse_xccdf.py + tests using a tiny fixture XCCDF.
Phase 1b: build_data.py reads a sample zip layout and writes data/ shape per DESIGN.md.
Phase 2a: Scaffold web/ Vite+TS app with routes and MetaBanner reading meta.json.
Phase 2b: Rule detail page + CopyButton citation format.
Phase 2c: MiniSearch worker over search/documents.json.
Phase 3: GitHub Actions Pages deploy + README quarterly update runbook.
```

## Parallel tools

- **External model review** — use `docs/EXTERNAL_REVIEW_PROMPT.md` before Phase 1.
- **Local verify** — always run build/tests yourself after agent claims done.
- **Git** — small commits per phase; never force-push shared main without reason.
