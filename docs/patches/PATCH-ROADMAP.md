# Exact edits for `ROADMAP.md`

`ROADMAP.md` was verified on 18 November 2026. Six repositories and one release have
appeared since. Apply these replacements, keep the rest of the document (it is the
best record of the corrections).

## 1. Header note

After the first paragraph, add:

```markdown
> **Update, 24 November 2026.** Six repositories have appeared since this audit —
> `nijatva-translate`, `nijatva-appstore`, `nijatva-appstore-catalog`, `nijatva-index`,
> `Nijatva-WorkSpace`, `nijatva-reader-engine` — plus `nijatva-photo-editor` v1.6.0.
> The F4 entry below and the Phase 0.1 order are out of date; `docs/APP-REGISTRY.json`
> is now the source of truth for app status.
```

## 2. Replace the F4 `nijatva-suite` table

| Item | Reality |
| --- | --- |
| Contents | `README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `LICENSE`, `index-v1.json`, `tools/generate_index.py`, `tools/index-policy.json`, `.github/workflows/index.yml`, `docs/` |
| Index | **Exists and is live.** One entry: Photo Editor 1.5.0, `versionCode` 6, sha256 `bce46bb2…f401c`, signer `CN=Vasudev Dangaya, O=Nijatva Photo Editor, C=IN` |
| Index freshness | **Stale by one release** — v1.6.0 is published, the index still serves 1.5.0 |
| Releases | 0 |

## 3. Replace the "Apps, in the two that matter most" closing line

The line "no app has ever produced a signed release build" is now **false**:

```markdown
So: Photo Editor 1.5.0 is the suite's first signed, indexed release. Everything else
still publishes debug APKs — browser under tag `latest`, camera under `*-debug` tags,
gallery as `v0.1.3-appearance-debug`. Ten of the eleven released apps cannot be
indexed until they ship a signed `assembleRelease` build under a real version tag.
```

## 4. Replace §4 Phase 0.1's reference app

`nijatva-notes` is not the right reference app: Photo Editor already has the only
signed, indexed entry and a working CI signing path. Replace "Build the index
generator in `nijatva-suite`…" with:

```markdown
### Phase 0.1 — One real release, end to end (blocking)

Reference app: `nijatva-photo-editor`.

1. Move the hardcoded `storePassword` / `keyPassword` out of
   `app/build.gradle.kts:24,26` into CI secrets.
2. Confirm the keystore is backed up outside GitHub; record the cert SHA-256.
3. `assembleRelease` v1.6.0 signed with the suite key, minified.
4. Re-index at 1.6.0 and prove an update from 1.5.0 on a physical phone.

Done when: a phone with 1.5.0 installed updates to 1.6.0 from the index URL, and the
build would have failed if a banned dependency were added.
```

## 5. Add to §2 corrections

```markdown
### 2.11 Hardcoded signing passwords

`nijatva-photo-editor/app/build.gradle.kts:24,26` carries `storePassword = "nijatva"`
and `keyPassword = "nijatva"` in a public repository. The keystore file itself comes
from a CI secret, so this is not a full compromise — but it halves the secret. Move
both values to `KEYSTORE_PASSWORD` / `KEY_PASSWORD`.

### 2.12 `apps.json` drift, again

`nijatva-core/tools/apps.json` lists 25 apps and 11 with a repo; reality is 32 tracked
and 19 with a repo (two of them, `nijatva-calc` and `nijatva-drive`, are not visible
to the GitHub App). It is now generated: `nijatva-core/tools/gen_apps_json.py` reads
`nijatva-suite/docs/APP-REGISTRY.json`. Do not hand-edit `apps.json`.
```
