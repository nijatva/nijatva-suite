# Nijatva — verified status, corrections and build order

Checked against the repositories on 18 November 2026 by reading them, not by
reading their READMEs. Every number below was counted from the repos.

This document replaces the status table in `ARCHITECTURE.md` §3, and it records
the claims that are currently wrong so they do not come back.

---

## 1. What actually exists

### Organisation

22 repositories: 15 app repositories, the 4 foundation repositories,
`nijatva.github.io`, `nijatva-web-store` and `.github`.

App repositories that exist: browser, browser-mini-x, notes, video-player,
video-player-multiplatform, photos, photo-editor, gallery, camera, music-player,
file, drive, dialer, contacts, messages. Fifteen of the 28 apps in
`apps.json` — four of them (photos, video-player, photo-editor, browser-mini-x)
were built outside the original 24-app plan.

### F1 `nijatva-core`

| Item | Reality |
| --- | --- |
| Modules | One: `:signature` |
| `:signature` | 9 Java classes, plain framework APIs, no dependencies, `minSdk 21`, `compileSdk 34`, publishes `com.nijatva:signature:1.0.0` to `mavenLocal` |
| Consumers | 2 of 15 apps, both imperfectly (see §2.5, §2.6) |
| Releases | 0 |
| Design system, SAF helpers, TTS wrapper, encrypted prefs, backup/restore | **Not written.** Described in `ARCHITECTURE.md` §5 and the GitHub description only. |
| `INTEROP.md` | A correct specification of intent-based app-to-app behaviour. It is a spec, not a module; nothing in it is code yet. |

### F2 `no-gms-check`

| Item | Reality |
| --- | --- |
| Code | Plugin, task, extension, 1 functional test, CI workflow on its own repo |
| Mechanism | Resolves compile/runtime classpaths and matches banned **group prefixes**, so transitives are caught. Stronger than a `build.gradle` text scan. |
| Banned groups | `com.google.android.gms`, `com.google.firebase`, `com.google.android.play`, `com.google.android.ads`, `com.google.android.tagmanager`, `com.crashlytics.sdk.android`, `com.google.ads.mediation` |
| Project-dependency rule | `allowedProjectDependencies` defaults to `:nijatva-core`, `:nijatva-design` — a rule about *sibling app* modules |
| Published | Nowhere. No release, no Gradle Plugin Portal, no GitHub Packages |
| Applied by apps | **0 of 15** |

### F3 `nijatva-design`

| Item | Reality |
| --- | --- |
| Icons | 30 icon sets, each with `icon.svg` + adaptive foreground/background/monochrome + `mipmap-anydpi-v26` wiring. `minSdk 26` assumption documented. Good state. |
| Templates, screenshot templates, brand assets | **Not present.** No directory, no file. |
| Design tokens (colour, type, spacing) | **Not present, and this is the right place for them to be absent.** Tokens belong in code (`core:design`), because an assets repository cannot be consumed as a dependency. |

### F4 `nijatva-suite`

| Item | Reality |
| --- | --- |
| Contents | `README.md`, `ARCHITECTURE.md`, `LICENSE` |
| Index | None. No `index-v1.json`, no generator, no Pages output. |
| Releases | 0 |

### Apps, in the two that matter most

| App | Reality |
| --- | --- |
| `nijatva-notes` | Uses `com.nijatva:signature:1.0.0` via `mavenLocal`. Has `gradlew`. 1 release. CI assembles a **debug** APK only. |
| `nijatva-browser` | Has a **committed AAR** at `app/libs/nijatva-signature-1.0.0.aar`. **No `gradlew`** (its CI comment says so). 6 releases, all tagged `latest`, all **debug** APKs. Its `build.yml` hand-rolls a GMS grep against `releaseRuntimeClasspath`. |

So: APKs exist and are downloadable, but no app has ever produced a signed
release build, and no release is indexed anywhere. The distribution channel is
the gap, not the binaries.

---

## 2. Corrections

Each entry: what is wrong, where it lives, and what to replace it with.

### 2.1 `nijatva-core` GitHub description overclaims

Current: *"Compose design system, storage helpers, encrypted preferences and
local backup — the shared library every Nijatva app is built on."*

Only the signature kit exists, and the app count is 2, not "every".

Replace with:

> Shared libraries for the Nijatva suite. Today: `:signature` — the Appearance
> and Developer screens every app carries, framework Java, no dependencies.

### 2.2 `nijatva-design` GitHub description overclaims

Current: *"Icons, screenshot templates and brand assets that keep twenty-four
separate apps looking like one suite."* Templates do not exist yet.

Replace with:

> Icon sources and adaptive-icon resources for the suite: one 96px SVG plus the
> drawable and mipmap wiring per app. Thirty sets so far.

### 2.3 `ARCHITECTURE.md` §3 status table is stale in both directions

It says Phase 0 is "Repos created, README only", Phase 1 is "4 of 5 repos
created", Phase 2/3 "Not started", and Phase 4 "Browser built, 182 files".
Reality: 15 app repos exist, spanning Phases 1, 2, 3 and 4; Foundation is
part-written, not README-only. Replace the whole table with §1 of this document
plus the build order in §4.

### 2.4 `nijatva-design` README says "thirty apps", the description says "twenty-four"

`nijatva-core/tools/apps.json` is the source of truth: **28 apps**, 14 with a
repository. Fix the design README line to "twenty-eight".

### 2.5 `apps.json` did not know about four apps that exist

`nijatva-core/tools/apps.json` listed 24 planned apps, 10 with a `repo` value.
Four app repositories existed with no entry at all: `nijatva-photos`,
`nijatva-video-player`, `nijatva-photo-editor` and `nijatva-browser-mini-x`. An
index generated from that file would have dropped four built apps without saying
so.

**Fixed.** The manifest now carries 28 apps, 14 with a repository, with the real
package names read from each app's build file. `SignatureDevInfo.java` was
regenerated from it, so the figures on the Developer screen finally match the
suite (22 repositories, 28 apps, 14 with code).

### 2.6 `nijatva-browser` commits a binary

`app/build.gradle.kts:59` — `implementation(files("libs/nijatva-signature-1.0.0.aar"))`.

This is the exact duplication `nijatva-core` exists to prevent: the AAR is now a
frozen copy that no core fix can reach, and it is invisible to dependency
tooling. Delete the file and switch to the published coordinate.

### 2.7 `nijatva-browser` reimplements the GMS check badly

Its `build.yml` greps `releaseRuntimeClasspath` for `com.google.android.gms|firebase|play-services`.
That misses `com.google.android.play`, the ads group, Tag Manager, Crashlytics
and mediation groups that the plugin bans, and it only looks at one
configuration. Every app doing this means 15 copies that drift. Delete the step;
apply the plugin (§4, Phase 0.2).

### 2.8 A debug APK published as `latest` is not a release

Browser publishes `assembleDebug` output under tag `latest`; notes publishes a
debug artifact. Debug builds are debuggable, unminified, use a debug signing
key, and cannot be updated to a release build later without uninstall. Before
the suite index goes live, each indexed app needs an `assembleRelease` build
signed with the suite keystore, and a real version tag.

### 2.9 Two dependency models are in play at once

The plugin's `allowedProjectDependencies` assumes core and design arrive as
**project** modules in the same build. Apps consume them as **Maven artifacts**
(`mavenLocal`, or a committed AAR). Pick one. Recommendation: published
artifacts, because 15 repositories cannot share a local path and CI has no
`mavenLocal`. Keep the project-dependency rule, but read it as what it says —
"an app must not depend on a sibling app module" — not as the delivery route for
core.

---

### 2.10 One app in the suite is not native, and that is a decision to make

`Vault` maps to `nijatva-drive`, which is a React Native app (Expo + TypeScript),
not a Kotlin/Compose one. That mapping is correct — it is the vault — but it has
consequences the rest of this document assumes away:

- it cannot consume `:signature`, `core:design` or any other core module, so it
  will never look like the rest of the suite unless it is rebuilt;
- `no-gms-check` cannot reason about its dependency tree the way it does for a
  Gradle Android app;
- its APK comes from the Expo build pipeline, so the index gate in `tools/` is
  the only place its promises are verified.

Either keep it and accept the different look, or put it on the list to rewrite
natively in Phase 3. Do not leave it as an unexamined exception.

---

## 3. Non-negotiables

1. No binary artifacts in git. No AARs, no APKs, no jars. Binaries live in
   Releases.
2. `mavenLocal` is a developer convenience, never the CI path. CI resolves from
   GitHub Packages.
3. `:signature` stays dependency-free (framework Java, `minSdk 21`). Anything
   needing AndroidX or Compose goes in a separate core module, so an app that
   only wants the signature screens does not inherit Room or Compose.
4. Every core module ships with at least one consumer in the same PR. A module
   with no consumer is a guess.
5. The keystore never enters a repository. One keystore for the suite, backed up
   outside GitHub, fingerprint recorded in the index generator.
6. Design tokens live in code (`core:design`). `nijatva-design` holds sources
   and generated resources only.
7. Icons are generated from `icon.svg` by a script, never hand-edited per app.

---

## 4. Build order, with a definition of done

### Phase 0.1 — Suite index and one real release (blocking)

Build the index generator in `nijatva-suite`: read `apps.json` + GitHub Releases,
emit an F-Droid-compatible index on Pages. Binaries stay in Releases, Pages
carries JSON and links only.

Done when: `nijatva-notes` ships a signed release APK under a version tag, the
index lists it with the correct signing fingerprint and `versionCode`, and it
installs and updates on a phone from the index URL. One app, end to end. The
same script then serves the other 23.

### Phase 0.2 — Distribution and enforcement

Publish `com.nijatva:signature` (and the plugin) to GitHub Packages; delete the
committed AAR; apply `no-gms-check` to all 15 app builds; delete the hand-rolled
grep in browser; add branch protection so the check is required.

Done when: `./gradlew check` in any app fails when a banned group is added, CI
proves it on a throwaway branch, and no app resolves core from a local path or a
committed file.

### Phase 0.3 — Core modules, in the order apps need them

1. `core:design` — Compose theme, the standard screen skeleton from
   `ARCHITECTURE.md` §2, colour/type/spacing tokens including the Indian accent
   set (terracotta, haldi, indigo), dark-mode safe.
2. `core:storage` — SAF helpers: pick a folder, persist the grant, stream a
   file, show an honest empty state on a revoked grant.
3. `core:logging` — rotating local log file in the app's private directory,
   viewer and export in Settings. This replaces crash reporting entirely.
4. `core:prefs` — encrypted preferences on AndroidKeyStore + AES-GCM, written by
   us. Do not use `androidx.security:security-crypto`: all its APIs were
   deprecated in April 2025 with no further releases, and Google's own guidance
   now points at `KeyGenerator` with `AndroidKeyStore`, or DataStore with the
   `datastore-tink` serializer. An "encrypted" label on a deprecated library is
   a liability in a privacy pitch.
5. `core:backup` — export and restore a whole app's data as one file.
6. `core:interop` — small helpers implementing `INTEROP.md`: safe
   `startActivity` with fallback, package visibility, sibling detection.
7. `core:tts` — thin wrapper, only when an app needs it.

Done when: each module has a consumer, and removing it from that consumer breaks
the build (that is how you know it is used).

### Phase 0.4 — Phase 1 apps

Calc, Clock, QR Scanner, Files. Notes exists; bring it onto the new core
modules first so the pattern is proven before three more apps copy it.

### Later

- Device-to-device transfer (Wi-Fi Direct / local HTTP, no internet): Phase 3,
  alongside Contacts and Vault. This is transfer, not sync — the suite has no
  sync, per `ARCHITECTURE.md` §5. Do not build it on NanoHTTPD: no active
  maintainer, no commits in six months, and an unpatched vulnerability report on
  record. Use an embedded Ktor server or a plain `ServerSocket` streaming into
  SAF.
- Store client app: after the index is live and at least five apps are indexed.
  Normal `PackageInstaller` with `REQUEST_INSTALL_PACKAGES` is enough; Shizuku
  is an optional power-user path, not the main one.

---

## 5. Open decision

Consumption model (§2.9): published artifacts or composite build. Everything in
Phase 0.2 depends on the answer, so decide it before touching the app builds.

---

Nijatva is built in India. Contact: Vasudev.work@rediffmail.com
