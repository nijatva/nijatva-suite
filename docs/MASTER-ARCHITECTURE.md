# MASTER-ARCHITECTURE.md

Nijatva — a local-first Android ecosystem, built in India.
**Verified: 24 November 2026.** Numbers here come from reading the repositories, not from READMEs. If this file disagrees with a repository, the repository wins and this file gets corrected.

---

## 1. What Nijatva is

Four components, one standard. Apps are the visible part; the other three exist so 30+ apps do not become 30 unrelated projects.

| Component | Repository | Responsibility | State today |
|---|---|---|---|
| Foundation | `nijatva-core` | Shared Android code: `:signature`, and later design, storage, prefs, backup, TTS | Only `:signature` exists |
| Design | `nijatva-design` | Icon sources + adaptive icon resources | 30 icon sets, no templates, no tokens |
| Security | `no-gms-check` | Gradle plugin + CI action that fails a build on banned groups | Complete, applied by 0 app builds |
| Distribution | `nijatva-suite` | App index (F-Droid style) on GitHub Pages, plus the policy docs | Index live with 1 app |

**Not part of the four, but part of the product:** `nijatva-appstore` (the store client), `nijatva-appstore-catalog`, `nijatva-index` (Python index service), `Nijatva-WorkSpace`, `nijatva-web-store`, `nijatva.github.io`.

---

## 2. Ecosystem map

```
                    NIJATVA
                       |
   +-------------------+-------------------+
   |                   |                   |
 APPS              PLATFORM            WORKSPACE
 (28 planned,      (core, design,      (isolation, work
  17 with repos,   no-gms-check,        profile, app
  11 released,     suite, appstore,     freezing)
  1 indexed)       index, Pages)
   |                   |                   |
   +---------+---------+---------+---------+
             |                   |
        GitHub Releases     index-v1.json
        (APK binaries)      (metadata only)
             |                   |
             +---------+---------+
                       |
                  GitHub Pages
                       |
                 App Store client
                       |
              SHA-256 verify -> PackageInstaller
```

Two rules the diagram encodes:

- **Binaries never enter git and never enter Pages.** Releases carry APKs; Pages carries JSON that points at them.
- **The index is the only gate.** If an app is not in `index-v1.json` with a verified signature and hash, it is not part of the suite, whatever its repo says.

---

## 3. Repository inventory (verified)

**27 repositories visible to the agent's GitHub App; at least 28 in total** — `nijatva-calc` is visible in the GitHub UI but returns 404 to the App, so App scope is incomplete. A 404 means "not visible", never "does not exist".

| Group | Count | Repositories |
|---|---|---|
| Foundation | 4 | `nijatva-core`, `nijatva-design`, `no-gms-check`, `nijatva-suite` |
| Apps | 17 | browser, browser-mini-x, camera, calc, contacts, dialer, file, gallery, messages, music-player, notes, photo-editor, photos, reader-engine, translate, video-player, video-player-multiplatform |
| Ecosystem | 7 | appstore, appstore-catalog, index, WorkSpace, github.io, web-store, `.github` |
| Unresolved | 1 | Vault documented as `nijatva-drive` — not visible to the App |

`APP-REGISTRY.json` is the machine-readable version of this table and is the single source of truth for app status.

### 3.1 Count reconciliation (read this before quoting a number)

| Claim | Reality |
|---|---|
| "28 apps" (ARCHITECTURE) | 24 in the phased plan + 4 built outside it (Photos, Video Player, Photo Editor, Browser Mini X) |
| "25 apps" (`nijatva-core/tools/apps.json`) | Stale: it omits the 4 above, plus Translate, Reader, App Store and WorkSpace; it also lists `nijatva-calc` and `nijatva-drive` as if the App could see them |
| "24 apps" (nijatva.github.io description) | Stale by the same 4 |
| Apps tracked now | **32** (28 + Translate, Reader, App Store, WorkSpace) |
| Apps with a repository | **17** (calc unverified) |
| Apps with any release | **11** |
| Apps indexed | **1** (Photo Editor 1.5.0) |
| Apps with a signed release | **1** |
| App builds applying `no-gms-check` | **1** (WorkSpace references it; core does too, but core is not an app) |

`apps.json` is the input to the index generator, so this drift is a **distribution bug**, not a documentation bug: an index generated from it silently drops apps that exist.

---

## 4. Standard app anatomy

Every app is one screen skeleton, so a user who learns one app knows all of them.

```
+------------------------------------------------------+
| [Top bar]  Nijatva Notes                 [ Offline ] |
+------------------------------------------------------+
| [Privacy banner]  SAF: granted | INTERNET: not req.  |
+------------------------------------------------------+
| [Primary surface]  editor / grid / dialpad / reader  |
+------------------------------------------------------+
| [Bottom]   [ Home ]   [ Vault / Local ]  [ Settings ]|
+------------------------------------------------------+
```

- The privacy state is **on screen**, not buried in Settings. "INTERNET: not requested" is a feature to display, not hide.
- The middle tab is `Vault / Local`. There is no `Cloud` tab, because there is no cloud.
- Every app carries the Appearance and Developer screens from `:signature`.
- UI stack varies today: Compose (Kotlin), View/Java, Compose Multiplatform (Music), React Native (Vault). The design system must therefore ship **tokens as XML resources plus a Compose wrapper** — see `DESIGN-SYSTEM.md` §2. A Compose-only design system cannot reach the six Java apps without rewriting them.

---

## 5. Distribution architecture

```
nijatva-suite/tools/generate_index.py
        |  reads apps.json + GitHub Releases API
        |  refuses: unsigned APK, wrong versionCode, targetSdk < 34, banned dex
        v
index-v1.json  (F-Droid v1 schema)
        |
        v
GitHub Pages  https://nijatva.github.io/nijatva-suite
        |
        v
nijatva-appstore (client)  ->  download APK  ->  verify sha256 + signer
        |
        v
PackageInstaller (system confirmation dialog — never silent)
```

Index policy today: `minTargetSdk: 34`, `extraBannedDex: {}`, `apps: {}`.
Index content today: one entry, Photo Editor 1.5.0, `versionCode` 6, sha256 `bce46bb2…f401c`, signer `CN=Vasudev Dangaya, O=Nijatva Photo Editor, C=IN`, minSdk 26, targetSdk 35, 4 ABIs, 6.5 MB.

**Index is stale:** `nijatva-photo-editor` has released v1.6.0 since, and the index still offers 1.5.0.

---

## 6. Platform capability — what a normal app can and cannot do

This section exists because the reference screenshots (privacy dashboard, permission manager, scrambled PIN, system app store) show features that belong to the **operating system**, not to an installable app. Building a promise the platform cannot keep is the fastest way to lose the privacy argument.

| Feature seen in the references | Can Nijatva build it as a normal app? | What is actually possible |
|---|---|---|
| Privacy Dashboard showing which apps used camera/mic/location in the last 24 h | **No** | Per-app access history is AppOps data, readable only by the OS or a privileged app. Nijatva can show: its own usage, installed apps' **declared/requested** permissions, and each app's targetSdk/tracker-profile. A "Nijatva Privacy Dashboard" must be labelled as a permission audit, not an access log |
| Permission manager ("17 of 60 apps allowed camera") | **Partly** | Requested permissions are readable via `PackageManager` with `QUERY_ALL_PACKAGES` (a Play-restricted permission, but fine for sideload). **Granted** runtime permissions of other apps are not readable by a third-party app |
| Scramble PIN layout, "power button instantly locks" | **No** | That is the system lock screen (GrapheneOS/CalyxOS style). A normal app cannot alter it. Nijatva can offer its own in-app lock (PIN + Keystore-bound key) for Vault and WorkSpace |
| Minimal launcher with app grid + search | **Yes** | `HOME` intent role + `QUERY_ALL_PACKAGES`; no privileged access needed |
| App store with updates | **Yes** | Index + `PackageInstaller` + `REQUEST_INSTALL_PACKAGES`. System confirmation is mandatory and must not be described as silent |
| Live "camera/mic in use" indicator | **No** | OS-only (status bar indicator). An app can only report its own use |

Anything marked **No** is either dropped or reframed in the store listing. It is never shipped as a half-working toggle.

---

## 7. Open decisions (blocking)

| # | Decision | Blocks | Recommendation |
|---|---|---|---|
| D1 | Consumption model for core: published Maven artifacts (GitHub Packages) vs composite build | Phase 0.2 and every app build | Published artifacts. `nijatva-core/publish.yml` already targets GitHub Packages; 15 repos cannot share `mavenLocal`, and CI has no local path |
| D2 | Reference app for Phase 0.1: `nijatva-notes` (ROADMAP) or `nijatva-photo-editor` (already indexed) | The whole phase order | **Photo Editor.** It already has the only indexed, signed entry and a working CI signing path. Update ROADMAP §4 to match, then make Notes the second |
| D3 | Vault: keep React Native, or native rewrite in Phase 3 | Vault, WorkSpace, design consistency | Keep for now, rewrite natively in Phase 3. Do not let it silently set a precedent |
| D4 | Does `nijatva-appstore` replace `nijatva-index`, or wrap it? | Store client scope | Store client consumes `index-v1.json`; `nijatva-index` stays a server-side helper or is archived |

---

## 8. Non-negotiables

Full list in `SECURITY-POLICY.md` §2 and `RELEASE-POLICY.md` §3. The five that shape architecture:

1. No sync, ever. Transfer (Wi-Fi Direct / local HTTP) is not sync.
2. No binary artifacts in git; no keystore in git.
3. `:signature` stays dependency-free (framework Java, `minSdk 21`).
4. Every core module ships with a consumer in the same PR.
5. Design tokens live in code and resources; `nijatva-design` holds sources only.

---

## 9. Document set

| File | Purpose |
|---|---|
| `MASTER-ARCHITECTURE.md` | This file — ecosystem, layers, capability limits, open decisions |
| `DEVELOPMENT-ROADMAP.md` | Phase-wise build order with "done when" tests |
| `APP-REGISTRY.json` | Machine-readable app and repo status (source of truth) |
| `SECURITY-POLICY.md` | Privacy, permissions, banned SDKs, keystore, audit |
| `RELEASE-POLICY.md` | Signing, versioning, CI gates, index rules |
| `DESIGN-SYSTEM.md` | Tokens, components, screen patterns, what the references can and cannot become |

*Nijatva is built in India. Contact: Vasudev.work@rediffmail.com*
