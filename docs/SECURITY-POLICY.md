# SECURITY-POLICY.md

Security and privacy rules for the Nijatva suite. Rules marked **MUST** are enforced in code review or CI; rules marked **MUST NOT** are grounds to reject a PR.

Verified against the repositories on **24 November 2026**.

---

## 1. Threat model

Who we defend against, in priority order:

| # | Adversary | What they want | What stops them |
|---|---|---|---|
| 1 | The app vendor's own future self | Adding "just one" analytics SDK to fix a crash | `no-gms-check` failing the build; no crash reporter to reach for |
| 2 | A network attacker | Content, metadata, or a malicious update | No network permission in most apps; index signer + sha256 check |
| 3 | A malicious app on the same device | Reading notes, photos, contacts | App-private storage, SAF, no shared world-readable dirs, encrypted prefs |
| 4 | Someone who gets the phone | The vault, the notes | In-app PIN + Keystore-bound key; no plaintext at rest in Vault |
| 5 | A supply-chain attacker | Injecting code through a dependency or a committed binary | Banned-group scan, no binaries in git, dependency review |
| 6 | The user's own curiosity about what we do | — | No telemetry to be curious about |

Explicitly **not** in the threat model: a rooted device with an unlocked bootloader, a state-level attacker with physical access, or Google itself. Say so in the store listing rather than implying otherwise.

---

## 2. Absolute rules

### 2.1 Banned dependencies (build fails)

`no-gms-check` matches **group prefixes** on the resolved compile and runtime classpaths, so transitives are caught:

```
com.google.android.gms          com.google.firebase
com.google.android.play         com.google.android.ads
com.google.android.tagmanager   com.crashlytics.sdk.android
com.google.ads.mediation
```

Also banned by policy even though a scanner cannot see them:

| Banned | Replacement |
|---|---|
| Firebase Cloud Messaging | UnifiedPush / ntfy / foreground WebSocket — most apps need no push at all |
| Crashlytics, Firebase Analytics | Nothing, or self-hosted Sentry; local log export via `core:logging` |
| AdMob / any ad SDK | Nothing. An ad SDK is a tracking SDK |
| Play Core in-app updates | Own index (`nijatva-suite`) |
| Play Services ML Kit | Bundled TFLite / whisper.cpp / Vosk, model shipped in the APK |
| Google Maps SDK, FusedLocationProvider | osmdroid / MapLibre + OSM; `LocationManager`; manual city entry |
| Google Sign-In | No account at all |
| `MANAGE_EXTERNAL_STORAGE` | Storage Access Framework, Photo Picker |
| `androidx.security:security-crypto` | `KeyGenerator` + `AndroidKeyStore` (AES-GCM), or DataStore with `datastore-tink`. All its APIs were deprecated April 2025 with no further releases |
| NanoHTTPD | Embedded Ktor, or `ServerSocket` streaming into SAF |

### 2.2 Binaries and secrets

- **MUST NOT** commit `.aar`, `.apk`, `.jar`, `.jks`, `.keystore`, or any keystore-adjacent file.
  Check: `git ls-files | grep -Ei '\.(aar|apk|jar|jks|keystore)$'` — must print nothing.
- **MUST NOT** hardcode a keystore path password, key password, API key or token in a build file. *(Current violation: `nijatva-photo-editor/app/build.gradle.kts:24,26` contains `storePassword = "nijatva"` and `keyPassword = "nijatva"`. Fix in Phase 0.1 task 1.)*
- **MUST NOT** put a keystore in GitHub Actions artifacts, caches or logs. Restore it from `KEYSTORE_BASE64` and delete the file in a `finally` step.
- **MUST** keep one keystore for the whole suite, backed up in two offline locations, with its SHA-256 fingerprint recorded in `RELEASE-POLICY.md` and in the index generator.

### 2.3 Data handling

| Rule | Detail |
|---|---|
| Local by default | All user data lives in app-private storage or a user-chosen SAF folder |
| No telemetry | No analytics, no crash upload, no "anonymous usage". The default log is local and exported only by the user |
| No accounts | No sign-in, no server-side identity, no device registration |
| No sync | Transfer between devices is user-initiated, direct, and never through a server |
| Encryption at rest | Sensitive stores (Vault, WorkSpace, encrypted prefs) use AES-GCM with a key in `AndroidKeyStore`, `setUserAuthenticationRequired(true)` where a lock exists |
| Screenshots | Vault and any screen showing a secret sets `FLAG_SECURE` |
| Clipboard | Sensitive fields clear the clipboard on exit and mark `EXTRA_IS_SENSITIVE` |
| EXIF | Stripped on share by Gallery and Photo Editor |

### 2.4 Permissions

Minimum, and justified in the store listing per app.

| App class | Allowed | Never |
|---|---|---|
| Calculator, Clock, Notes, QR, PDF, Device Info, Expenses, Tasks, Keyboard | Storage via SAF only | INTERNET, location, contacts |
| Gallery, Photos, Camera, Music, Video | `READ_MEDIA_*`, `CAMERA` | `MANAGE_EXTERNAL_STORAGE`, location |
| Dialer, Contacts, Messages | `READ_CONTACTS`, `CALL_PHONE`, `READ_SMS`/`SEND_SMS` **only as default handler** | INTERNET |
| Browser | INTERNET, `POST_NOTIFICATIONS` (optional) | location by default, `READ_CONTACTS` |
| Vault, WorkSpace | `USE_BIOMETRIC`, `QUERY_ALL_PACKAGES` (WorkSpace) | INTERNET |

Every app's on-screen privacy banner states its own permission truth. A banner that lies is worse than no banner.

---

## 3. Per-app audit checklist

Run before an app is indexed. Each line is a yes/no a stranger can verify.

1. `git ls-files` shows no binary and no keystore.
2. `no-gms-check` runs in the app's CI and passes.
3. `AndroidManifest.xml` requests no permission outside the table in §2.4.
4. No `INTERNET` permission unless the app's role requires it.
5. `targetSdk >= 34`, `minSdk` documented.
6. Release build is minified and signed with the suite key; `applicationIdSuffix` is absent from release.
7. `android:debuggable` is not set in release; `android:allowBackup` is a deliberate choice, not a default.
8. `exported` is set explicitly on every component that declares an intent filter.
9. No hardcoded secret, URL with a token, or password in source.
10. Log statements in release do not print user content or paths.
11. Storage access goes through SAF; a revoked grant shows an empty state, not a crash.
12. Every third-party dependency has a licence compatible with Apache-2.0 and is listed in the app's `NOTICE`.
13. Store listing states permissions, minSdk, size and what the app does **not** do.
14. `sha256` in the index matches the published APK, and the signer fingerprint matches the suite key.

An app that fails any line is not indexed, however good it looks.

---

## 4. Vulnerability and incident response

| Situation | Action |
|---|---|
| A banned SDK appears in a dependency | CI fails. Do not "temporarily" allow-list it; find another library or drop the feature |
| A dependency publishes a CVE | Patch within 7 days for a released app; re-release and re-index |
| A secret is committed | Rotate it immediately, purge history, re-release if it was a signing credential. A password in a public repo counts as leaked |
| The signing key is suspected compromised | Stop releases, publish an advisory, ship a migration path (new package id or a signed migration build), revoke the old fingerprint from the index |
| A user reports data loss | Local logs + `core:backup` export; no server-side recovery exists, and the listing says so |

---

## 5. Honesty rules (these are security rules too)

- Do not claim a feature the platform cannot deliver — see `MASTER-ARCHITECTURE.md` §6. A privacy dashboard that shows only requested permissions must be called that.
- Do not describe debug-signed APKs as releases.
- Do not describe a repo as an app. Repo ≠ release ≠ indexed.
- Do not state a number (apps, downloads, users) that the repositories do not support.
- Do not promise dates. Timelines are floors.

---

## 6. What this policy deliberately does not do

- It does not use an "encrypted" library we cannot audit or that is deprecated.
- It does not add a crash reporter, even self-hosted, until `core:logging` exists and is the default.
- It does not defend against a rooted device; the listing says so.
- It does not store anything in the cloud, so there is no cloud breach to respond to.

---

*Owner: Vasudev. Changes to §2 need an explicit decision, not a PR comment.*
