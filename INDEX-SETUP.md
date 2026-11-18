# Nijatva index — setup and rules

`index-v1.json` is the file the store client reads to know what exists, what the
current version is, and whether an APK is the one you published. It is built
from GitHub Releases, so no server, no hosting bill and no third party is
involved.

## What is enforced on every APK before it can be indexed

An artifact is refused if it:

- is a **debug build** (`application-debuggable`)
- contains Play Services, Firebase, any advertising SDK, any billing library, any
  crypto-mining code, or a known tracker (byte-scanned in the real `classes*.dex`)
- declares `MANAGE_EXTERNAL_STORAGE` or `com.android.vending.BILLING`
- targets below **SDK 34**
- has a signing certificate that differs from the one recorded for that app
- carries a `versionCode` below the published one, or the same `versionCode` with
  different bytes (a downgrade, or an artifact swapped under a version that is
  already out)

A refusal is a warning: the index is written with everything that passed. That
keeps the suite usable while apps are still filling up — most have no release yet,
and their first one is expected to fail a gate.

One case is an error rather than a warning. If a package that is already in the
published index stops passing, the run fails and nothing is published: an app a
user already has must never quietly disappear from the store.

## Files

| File | Purpose |
| --- | --- |
| `tools/generate_index.py` | The generator. Python 3.12, standard library only. |
| `tools/index-policy.json` | `minTargetSdk`, extra banned strings, per-app overrides. |
| `.github/workflows/index.yml` | Runs it daily, on demand, and on `repository_dispatch`. |

## One-time setup

1. **Pages.** Repository → Settings → Pages → Source: *Deploy from a branch*,
   branch `main`, folder `/ (root)`. The index is then at
   `https://nijatva.github.io/nijatva-suite/index-v1.json`.
2. **Nothing else.** The app repositories are public, so the generator reads
   their releases anonymously. 15 repos at one or two pages each is well inside
   the 60 requests an hour that unauthenticated GitHub allows.
3. **Optional:** if the rate limit ever bites, create a fine-grained token with
   read-only `Contents` on the app repositories and save it as the secret
   `SUITE_INDEX_TOKEN`. The workflow passes it automatically; without it the
   run is anonymous and still works.

No keystore is needed for the index itself. The APK signing key stays where it
belongs: outside every repository, backed up, and never in CI logs.

## What each app must do to be indexed

1. Build `assembleRelease` and sign with the suite key. A debug APK will be
   refused by name, not silently published.
2. Tag the release with a version: `v1.2.0`. Rolling tags like `latest` are
   skipped on purpose — they cannot express "is this newer than what I have".
3. Attach **exactly one** APK to the release. If a release must carry several
   ABIs, name one of them `universal`.
4. Keep `targetSdk` at 34 or above.
5. First release only: after the first successful run, copy the `sig` value from
   `index-v1.json` for that package into `tools/index-policy.json`:

```json
{
  "apps": {
    "in.nijatva.notes": { "signingSha256": "<the 64 hex characters from sig>" }
  }
}
```

From then on, an APK signed with any other key is refused. This is the check
that makes an update an update and not a takeover.

## Per-app escape hatches, with a reason attached

If an app legitimately carries a banned string — a browser shipping an ad-block
list inside its dex, for instance — turn the scan off for that package only:

```json
{ "apps": { "in.nijatva.browser": { "allowDexScanOff": true } } }
```

Write down why, in the same file, next to it. A silent override is how a promise
becomes a rumour.

## Before the first run

`tools/apps.json` in `nijatva-core` must be reconciled first. As of 18 November
2026 it has no entry at all for four existing apps (photos, video-player,
photo-editor, browser-mini-x) and maps `Vault` to `nijatva-drive`, which is a
TypeScript project. An index built from it would drop four apps and ship one
wrong link.

## Running it locally

```sh
ANDROID_HOME=$HOME/Android/Sdk \
python3 tools/generate_index.py \
  --apps ../nijatva-core/tools/apps.json \
  --previous index-v1.json \
  --dry-run
```

`--dry-run` downloads and checks everything, prints every refusal with its
reason, and writes nothing.

## One honest limitation

This index is F-Droid **shaped**, not F-Droid **compatible** in the strict sense.
A stock F-Droid client expects the APK bytes to live under the repository URL and
expects a signed `index-v1.jar` next to the JSON. Here the bytes stay in GitHub
Releases and the client follows `apkUrl`, pinning the APK signing certificate
instead — which is the check that actually protects a user. If stock-client
compatibility is ever wanted, it is two additions: mirror the APKs under Pages
and sign the jar with a repository key. Neither changes the generator's output
shape, which is why `apkName` is kept alongside `apkUrl`.
