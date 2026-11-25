# DEVELOPMENT-ROADMAP.md

Build order for Nijatva. Every phase has a **done-when** test that can be checked by a stranger, not a feeling.
Verified starting point: **24 November 2026**.

---

## 0. The one sentence this roadmap enforces

Nijatva does not need more apps. It needs **one app that installs and updates from the index, signed, end to end** — and then the same pipeline for the rest.

Today: 17 app repositories, 11 with releases, **1 indexed, 1 signed, 0 apps running `no-gms-check`**.

---

## 1. Priority order (corrected)

The plan that prompted this document listed "audit all repositories" as priority 1 and "Photo Editor signing security" as 2. That order is wrong in one respect: the audit is a **day-long read**, the signing secret is a **live exposure**. Fix the exposure first.

| # | Task | Why this order | Time |
|---|---|---|---|
| 1 | **Keystore secret hygiene** — remove the hardcoded passwords `nijatva` from `nijatva-photo-editor/app/build.gradle.kts:24,26` and read them from CI secrets | A public repo currently publishes the store and key passwords for the only signing key in the suite. The keystore file itself is secret-only, so this is not yet a full compromise — but it halves the secret | 30 min |
| 2 | **Verify the keystore is backed up** outside GitHub, and record its SHA-256 fingerprint in the repo | If the key is lost, every installed app can never be updated, only uninstalled | 15 min |
| 3 | **Re-index Photo Editor at 1.6.0** (index is on 1.5.0) and prove install + update on a phone | This is Phase 0.1's actual done test | 2 h |
| 4 | **Fix `apps.json` drift** (25 apps / 11 repos vs reality 32 / 17) | The index generator reads it; drift silently drops apps | 2 h |
| 5 | **Apply `no-gms-check` to all app builds**, delete the committed AAR in `nijatva-browser`, delete its hand-rolled grep | Makes the privacy claim a build failure instead of a promise | 1–2 days |
| 6 | **Publish `com.nijatva:signature` to GitHub Packages** and switch apps off `mavenLocal` / committed AAR | Decides D1, unblocks everything in Phase 0.2 | 1 day |
| 7 | **`core:design` + `core:storage`** with one consumer each | Without them, 20 apps grow 20 copies of the same helper | 1 week |
| 8 | **Store client (`nijatva-appstore`) against the live index** | Only after ≥5 apps are indexed; before that it demos an empty shelf | 1 week |
| 9 | Remaining apps, in phase order | — | — |

Tasks 1–4 are one working day and change the suite's status from "claims" to "works". Do them before anything else.

---

## 2. Phases

### Phase 0.0 — Truth pass (done in this document set)

- [x] Repository inventory verified, drift recorded
- [x] `APP-REGISTRY.json` published as source of truth
- [ ] `nijatva-core/tools/apps.json` rewritten from the registry
- [ ] `nijatva-suite/README.md` and `ROADMAP.md` stale lines corrected

**Done when:** no document in the organisation states a number that the repositories contradict.

---

### Phase 0.1 — One real release, end to end (BLOCKING)

Reference app: **`nijatva-photo-editor`** (change from `nijatva-notes` — it already has the only signed, indexed entry and a working CI signing path; Notes becomes the second app on the pipeline).

- [ ] Signing passwords out of `build.gradle.kts`, into `KEYSTORE_PASSWORD` / `KEY_PASSWORD` secrets
- [ ] `isMinifyEnabled = true` with a working ProGuard/R8 config for release
- [ ] `assembleRelease` APK under tag `v1.6.0`, signed with the suite key
- [ ] Index entry updated: versionCode, versionName, sha256, signer fingerprint, minSdk, permissions
- [ ] Installed on a physical phone from the index URL, then **updated** from 1.5.0 → 1.6.0 without uninstall
- [ ] `no-gms-check` runs in the same workflow and fails on a planted banned dependency

**Done when:** a phone with 1.5.0 installed shows an update to 1.6.0 sourced from `https://nijatva.github.io/nijatva-suite`, and the build would have failed if `com.google.android.gms` were added.

---

### Phase 0.2 — Distribution and enforcement

- [ ] `com.nijatva:signature` on GitHub Packages; `mavenLocal` gone from CI
- [ ] Committed AAR deleted from `nijatva-browser`; it uses the published coordinate
- [ ] Hand-rolled GMS grep deleted from `nijatva-browser/build.yml`
- [ ] `no-gms-check` applied to all app builds (17), branch protection makes it required
- [ ] Plugin published to GitHub Packages (Plugin Portal optional)
- [ ] Index generator refuses: unsigned APK, debug-signed APK, `targetSdk < 34`, banned dex, missing source URL

**Done when:** adding `implementation("com.google.firebase:firebase-analytics")` to any app fails CI without anyone reviewing it.

---

### Phase 0.3 — Core modules, in the order apps need them

Each ships **with a consumer in the same PR**; removing the module must break that consumer's build.

| Order | Module | Contents | First consumer |
|---|---|---|---|
| 1 | `core:design` | Compose theme + XML tokens + standard skeleton | Photo Editor |
| 2 | `core:storage` | SAF folder pick, persisted grant, streaming, honest empty state | Files |
| 3 | `core:logging` | Rotating local log, viewer + export in Settings (replaces crash reporting) | Photo Editor |
| 4 | `core:prefs` | AES-GCM over `AndroidKeyStore`, written by us. **Not** `androidx.security:security-crypto` (deprecated April 2025) | Vault/WorkSpace |
| 5 | `core:backup` | Export/restore one app's data as a single file | Notes |
| 6 | `core:interop` | Safe `startActivity` with fallback, package visibility, sibling detection (implements `INTEROP.md`) | Dialer ↔ Contacts |
| 7 | `core:tts` | Thin wrapper, only when an app needs it | Reader / Browser |

**Done when:** each module has one consumer, and a deliberate API break fails that consumer's build in CI.

---

### Phase 1 — Small apps (Calc, Clock, Notes, QR, Files)

| App | State | Next |
|---|---|---|
| Notes | released v0.3.0, CI builds debug only | second app on the signed pipeline |
| Files | code, no releases, no CI | add CI + first release |
| Calculator | repo not visible to the App | verify, then add CI |
| Clock | no repo | build after `core:design` exists |
| QR | no repo | build last; smallest surface |

**Done when:** all five are indexed and update from the index.

---

### Phase 2 — Media (Gallery, Music, Recorder, PDF, Device Info, Weather)

| App | State | Note |
|---|---|---|
| Gallery | debug release only (`v0.1.3-appearance-debug`) | needs release signing; Kotlin without Compose |
| Music | 2 releases, Compose Multiplatform | desktop/web builds share the code |
| Photo Editor | indexed, signed | the reference app |
| Photos | 1 release, no CI | overlaps Gallery — decide which is canonical |
| Video Player | code, no releases | Media3 |
| Recorder | no repo | needs `core:storage` first |
| PDF | no repo | PDF viewing already exists inside `nijatva-file`; extract or leave |
| Device Info | no repo | read-only, no permissions |
| Weather | no repo | **manual city entry only**, no location, no third-party API key in the app |

**Done when:** no media app requests `MANAGE_EXTERNAL_STORAGE`, and each release is signed.

---

### Phase 3 — Phone roles (Dialer, Contacts, Messages, Calendar, Camera, Expenses, Tasks, RSS, Vault)

Highest-risk phase: telephony, SMS and contacts permissions are the ones users judge hardest, and `READ_SMS`/`CALL_LOG` need a default-app role.

| App | State |
|---|---|
| Dialer | 4 releases, no CI workflow |
| Contacts | 4 releases, no CI workflow |
| Messages | 4 releases, no CI workflow |
| Camera | 13 releases, **every tag ends in `-debug`** |
| Vault | React Native (`nijatva-drive`), repo not visible to the App |
| Calendar, Expenses, Tasks, RSS | no repo |

**Done when:** dialer/contacts/messages/calendar each hold their default-app role on a clean device, and each is signed + indexed.

---

### Phase 4 — Flagship (Keyboard, Launcher, Browser, App Manager)

| App | State |
|---|---|
| Browser | 6 releases, committed AAR, no `gradlew`, hand-rolled GMS grep |
| Browser Mini X | 1 release tagged `latest` |
| Keyboard | no repo — must never request INTERNET |
| Launcher | no repo — needs `QUERY_ALL_PACKAGES` |
| App Manager | no repo — partly exists inside `nijatva-file` |

---

## 3. Cross-cutting workstreams

| Workstream | Trigger | Owner decision |
|---|---|---|
| Device-to-device transfer (Wi-Fi Direct / local HTTP, no internet) | Phase 3, alongside Contacts and Vault | Not NanoHTTPD (unmaintained, unpatched report on record). Embedded Ktor or `ServerSocket` into SAF |
| Store client | ≥5 apps indexed | `PackageInstaller` + `REQUEST_INSTALL_PACKAGES`; Shizuku optional |
| WorkSpace | Phase 3 | isolation + freezing; already references `no-gms-check` |
| Local Backup & Restore | after `core:backup` | app or core screen — decide once |
| Website (`nijatva.github.io`) | continuous | must read its numbers from `APP-REGISTRY.json`, not hardcode "24 apps" |

---

## 4. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Signing key lost or leaked | Suite can never update installed apps | Offline backup ×2, fingerprint recorded, passwords only in CI secrets |
| Index generated from stale `apps.json` | Built apps silently disappear from the store | Registry → `apps.json` generated, not hand-edited; CI diff check |
| Core modules land late | 20 apps × duplicated SAF/design code | `core:design` + `core:storage` before any new app |
| Compose-only design system | 6 Java apps cannot consume it | XML tokens + Compose wrapper (`DESIGN-SYSTEM.md` §2) |
| Vault stays React Native | Looks foreign, cannot use core | Stated exception, native rewrite scheduled Phase 3 |
| Doc drift (already happened 3×) | Agents and contributors build on false facts | One source of truth (`APP-REGISTRY.json`), regenerated on release |
| Over-promising OS features | Privacy claim collapses under scrutiny | `MASTER-ARCHITECTURE.md` §6 is the ceiling; nothing ships above it |

---

## 5. What not to build yet

- No new app repositories until `core:design` and `core:storage` have consumers.
- No sync, no cloud, no accounts — not as "coming soon", not at all.
- No store client before 5 indexed apps.
- No privileged-app features (access logs, system lock screen) unless the app is a system app.
- No second browser, second gallery, second photo editor until the existing pair is resolved (Photos vs Gallery, Browser vs Mini X).

---

*Timelines assume part-time work and are floors, not promises. Re-verify this file against the repositories every two weeks.*
