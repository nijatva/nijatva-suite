# Exact edits for `README.md`

## Replace the Status section

Current text says the index is not published yet. Replace the whole **Status** section with:

```markdown
## Status

The index generator lives in `tools/generate_index.py` and runs from
`.github/workflows/index.yml`. What it refuses to index is in `INDEX-SETUP.md`.

The index is live at <https://nijatva.github.io/nijatva-suite> and currently carries
one app: Nijatva Photo Editor 1.5.0 (`versionCode` 6, signed, sha256 and signer
recorded). `nijatva-photo-editor` has since released 1.6.0, so the index is one
release behind — re-indexing is the next task.

`docs/APP-REGISTRY.json` is the source of truth for what exists in the suite:
32 apps tracked, 19 with a repository, 11 with releases, 1 indexed.

- [ROADMAP.md](ROADMAP.md) — verified status and corrections to earlier claims
- [docs/MASTER-ARCHITECTURE.md](docs/MASTER-ARCHITECTURE.md) — ecosystem, layers, platform limits
- [docs/DEVELOPMENT-ROADMAP.md](docs/DEVELOPMENT-ROADMAP.md) — build order with done-when tests
- [docs/SECURITY-POLICY.md](docs/SECURITY-POLICY.md) — privacy, permissions, banned dependencies
- [docs/RELEASE-POLICY.md](docs/RELEASE-POLICY.md) — signing, tagging, index rules
- [docs/DESIGN-SYSTEM.md](docs/DESIGN-SYSTEM.md) — tokens, components, screen specs
```

## Add to the top, under the title

```markdown
> **For coding agents:** read [AGENTS.md](AGENTS.md) before changing anything.
```

## Keep unchanged

The "Why this exists first" section and the licence note are still accurate.
