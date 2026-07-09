# stigref — Architecture Notes

Companion to [DESIGN.md](./DESIGN.md). Implementation-oriented.

## Runtime topology

```
Browser
  ├─ app shell (HTML/JS/CSS from Pages)
  ├─ GET data/meta.json
  ├─ GET data/search/documents.json  → MiniSearch (Worker)
  ├─ GET data/stigs/index.json
  └─ GET data/stigs|rules|controls/by-id/*.json  (on navigation)
```

No cookies, no auth, no write path.

## Parser (scripts)

Port ideas from rmfdb’s XCCDF handling without Flask/SQLAlchemy:

- Namespace: XCCDF 1.1
- STIG: title, description, version, release, release date
- Group/Rule: ids, severity, title, check, fix, CCI refs, metadata blobs as needed
- Deterministic STIG id generation
- Content hash of source ZIP → skip rebuild if unchanged

## Frontend modules (planned)

```
web/src/
  main.ts
  app.css
  lib/data.ts          # fetch helpers, base URL
  lib/search/worker.ts
  lib/copy.ts          # clipboard + citation formatters
  routes/
    Home / Search
    StigList / StigDetail
    RuleDetail
    ControlList / ControlDetail
    About
  components/
    SearchBox
    ResultList
    CopyButton
    MetaBanner
    LoadingErrorEmpty
```

## Pages SPA fallback

- Build emits `404.html` = `index.html` (GitHub Pages path reload support)
- Or hash routing if path mode proves painful (prefer path for clean links)

## Security / compliance notes

- Only process `U_` public packages
- Do not commit raw DISA ZIP if policy prefers not to (default: gitignore `raw/`)
- No secrets required for site runtime
- Supply chain: pin script deps; Actions pin action SHAs when possible
