# No-GMS — the definition

**Status:** proposed, 26 November 2026. This document is the single definition. If a tool, a policy
file or a store listing disagrees with it, this file wins and the other one is fixed.

---

## 1. The claim, in one testable sentence

> **No Nijatva app depends on, bundles, or calls Google Play Services, Firebase, Play Core, or any
> advertising or analytics SDK — at build time, at runtime, or inside the shipped APK.**

Everything below exists to make that sentence **checkable**, so the claim never becomes a marketing
word again.

---

## 2. What is banned — exact, mechanical

A dependency is banned when its **group id** starts with any of these:

| Group prefix | What it is |
|---|---|
| `com.google.android.gms` | Play Services (maps, location, auth, ML Kit Play variant, cast…) |
| `com.google.firebase` | Firebase (Crashlytics deps, Analytics, FCM, Firestore…) |
| `com.google.android.play` | Play Core (in-app updates, in-app review, split install) |
| `com.google.android.ads` | Mobile Ads SDK |
| `com.google.android.tagmanager` | Tag Manager |
| `com.crashlytics.sdk.android` | Crashlytics |
| `com.google.ads.mediation` | Ad mediation adapters |
| `com.amplitude`, `com.facebook.ads`, `com.appsflyer`, `com.mixpanel` | analytics/attribution SDKs |

Same list is matched as **strings inside the dex** at ship time, because a copied SDK or a
reflection-loaded one never appears on a Gradle classpath.

---

## 3. What is **allowed** — and this is the part that prevents future arguments

Google authors a lot of code that is **not** Play Services. Banning it would be wrong, and
un-banning it later would look like a policy retreat. So the allow-list is explicit:

| Allowed | Why it is not GMS |
|---|---|
| `androidx.*` (everything) | Android Jetpack; no Play Services, no Google account, works on AOSP |
| `com.google.android.material` | Material Components for Android — a UI library, not GMS |
| `com.google.code.gson` | JSON parser |
| `com.google.zxing` | Barcode/QR encoding — pure Java |
| `com.google.guava` | Utility library |
| `com.google.android.flexbox` | Layout manager |
| `org.jetbrains.*`, `org.json`, `okhttp3`, `coil`, `kotlinx.*` | not Google at all |

**The test that decides a borderline case** — a library is allowed only if all four are true:

1. It resolves and runs with **no** `com.google.android.gms.*` class on the classpath.
2. It declares no `<uses-library android:name="com.google.android.maps">` and no
   `com.google.android.gms.version` metadata in the manifest.
3. It needs **no Google account** and calls **no Google endpoint** at runtime.
4. The app still works on an **AOSP image with no Play Services installed**.

If a library passes those four, it is allowed whatever its group id is. If it fails any one, it is
banned whatever its documentation claims.

---

## 4. What the claim does **not** mean — say this out loud

| Not this | Why |
|---|---|
| "No Google-authored code" | Material Components and Gson are Google's; they are allowed |
| "No internet" | The browser, translate and weather apps use the network by design |
| "Cannot install on a Play device" | It installs and runs; it simply does not need Play Services |
| "No trackers of any kind" | The dex scan covers the banned list; a self-written logger is allowed if it stays local |
| "Verified by Google" | Nobody verifies this but our own CI — which is the point |

**The user-facing sentence** (store listing, website, README), and nothing stronger:

> No Google Play Services. No Firebase. No ads. No analytics. No accounts. Works offline.

---

## 5. Three enforcement layers — what each catches, and its blind spot

| Layer | Tool | Catches | Blind spot |
|---|---|---|---|
| **Build** | `nijatva-guard` plugin on resolved classpaths | transitive GMS/Firebase pulled in by another library | copied source, reflection, a renamed fork |
| **Ship** | `njqa` scanning dex strings in the built APK | copied SDKs, reflection-loaded classes, an APK built elsewhere | code that never uses the literal string |
| **Publish** | `index-policy.json` → `extraBannedDex` | a bad APK reaching the store | APKs served outside the index |

All three must be on. One layer is a promise; three are a claim.

**Currently:** build layer on **1** app of 17, ship layer on **1**, publish layer has an **empty**
`extraBannedDex`. So today the claim is unenforced — that is the actual problem, not the wording.

---

## 6. What a developer does when they want a library

```
Want to add a dependency
        │
        ├─ group starts with a banned prefix?  ── yes ──► STOP. Find an alternative.
        │                                                (see §7)
        └─ no
             │
             ├─ passes the four tests in §3?  ── no ──► banned, even if the docs say otherwise
             └─ yes
                  │
                  └─ add it. CI proves the decision in three places.
```

---

## 7. Replacements, decided once so nobody argues again

| Need | Do not use | Use |
|---|---|---|
| Push notifications | FCM | UnifiedPush / ntfy / foreground WebSocket |
| Crash reporting | Crashlytics, Firebase | `core:logging` local rotating log + user-exported file |
| Analytics | Firebase Analytics, Amplitude | nothing. Issues and the device checklist |
| Ads | AdMob | nothing |
| In-app updates | Play Core | our index (`nijatva-suite`) |
| On-device ML | Play-variant ML Kit | bundled TFLite / whisper.cpp / Vosk |
| Maps | Google Maps SDK | osmdroid / MapLibre + OSM tiles |
| Location | FusedLocationProvider | `LocationManager`, or manual city entry |
| Sign-in | Google Sign-In | no account at all |
| Storage | `MANAGE_EXTERNAL_STORAGE` | SAF, Photo Picker |
| Encrypted prefs | `androidx.security:security-crypto` | `KeyGenerator` + `AndroidKeyStore` (AES-GCM) |
| Local HTTP server | NanoHTTPD | Ktor, or `ServerSocket` into SAF |

---

## 8. How the definition is tested — positive and negative cases

A gate nobody has seen fail is not a gate. These cases belong in `nijatva-guard`'s test suite:

| Case | Dependency | Expected |
|---|---|---|
| 1 | `com.google.code.gson:gson` | **pass** (allowed Google code) |
| 2 | `com.google.android.material:material` | **pass** |
| 3 | `com.google.zxing:core` | **pass** |
| 4 | `com.google.firebase:firebase-analytics` | **fail** — Firebase |
| 5 | `com.google.android.gms:play-services-maps` | **fail** — Play Services |
| 6 | `com.google.android.play:app-update` | **fail** — Play Core |
| 7 | `com.google.android.gms:play-services-ads` | **fail** — ads |
| 8 | a library that pulls Firebase transitively | **fail** — transitives are the point |
| 9 | `com.google.zxing:core` + copied `com.google.firebase` classes in the APK | build **pass**, `njqa` **fail** |

Case 9 is the one that proves the layers are not redundant.

---

## 9. What cannot be enforced by a build

| Thing | Why | Where it goes |
|---|---|---|
| A library that talks to Google servers without GMS classes | no classpath evidence; needs traffic analysis | review + the store listing's honest wording |
| Whether the app **behaves** correctly without Play Services | needs a device | device checklist: install on an AOSP image, run the main flow |
| Whether a copied SDK is used at runtime | static scan sees strings, not behaviour | code review |

So the honest full claim is: **"no Play Services dependency, proven at build, ship and publish; and
verified to run on a device without them."** The last clause is a human check, and the checklist says so.

---

## 10. What changes today

| # | Change | File |
|---|---|---|
| 1 | This definition becomes the only one; SECURITY-POLICY §2.1 links to it | `nijatva-suite/docs/` |
| 2 | `extraBannedDex` filled with the §2 list | `nijatva-suite/tools/index-policy.json` |
| 3 | `njqa` default changed: a permission outside the allow-list is a **failure**, not a warning | `nijatva-qa/njqa.py` |
| 4 | Plugin published, then applied by all 17 apps | `nijatva-guard` + app repos |
| 5 | Positive/negative cases from §8 added to the plugin's tests | `nijatva-guard/src/test` |
| 6 | Store listing sentence replaced with §4 wording | `nijatva-suite` + website |

Until #3 and #4 are done, the claim is **stated, not enforced** — and this document says so rather
than pretending otherwise.
