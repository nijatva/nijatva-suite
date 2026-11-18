# nijatva-suite — Nijatva

**Meta repository**

The app index and the self-hosted repository index, served from GitHub Pages. APKs stay
in each app's own GitHub Releases; this repository carries only the JSON that points at
them.

## Why this exists first

This is the distribution channel. It replaces the Play Store role for the suite.

Part of the [Nijatva](https://nijatva.github.io) suite.

## Status

The index generator lives in `tools/generate_index.py` and runs from
`.github/workflows/index.yml`. What it refuses to index, and the one-time setup, are in
[INDEX-SETUP.md](INDEX-SETUP.md). [ROADMAP.md](ROADMAP.md) carries the verified status of
the whole suite and the corrections to earlier claims.

No index is published yet: the first entry waits for a signed release of `nijatva-notes`.

## Licence

Apache-2.0 for the code, as in [LICENSE](LICENSE). The name "Nijatva" and the app icons are
not covered by that licence — a fork must use its own name and its own icon.
