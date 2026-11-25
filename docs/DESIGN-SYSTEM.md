# DESIGN-SYSTEM.md — v2

One look across 30+ apps, delivered in a way that the six Java apps can actually consume.
**v2 (24 Nov 2026)** adds the full 17-screen reference catalogue: store, launcher, app manager, privacy report, appearance.

Companion to `MASTER-ARCHITECTURE.md` §4/§6 and `SECURITY-POLICY.md` §2.

---

## 1. The problem this document solves

The plan says "Kotlin + Jetpack Compose + Material 3 for every app". The repositories say something else:

| UI stack | Apps |
|---|---|
| Kotlin + Compose | camera, calc, gallery, music, photo-editor, photos, reader-engine, translate, video-player, browser, browser-mini-x, appstore |
| Java + Android Views (some without AndroidX) | dialer, contacts, messages, notes, file, WorkSpace |
| Compose Multiplatform | music-player, video-player-multiplatform |
| React Native | Vault (`nijatva-drive`) |

A Compose-only design system reaches **half the suite**. So the system ships twice from one source:

```
        nijatva-design (sources)
        ├── tokens/tokens.json          <- single source of truth
        ├── icons/*/icon.svg            <- 30 sets, generated
        └── scripts/gen_tokens.py
                     |
        +------------+-------------+
        |                          |
 core:design-android         nijatva-design (resources)
 Compose theme + components  colors.xml, dimens.xml, styles.xml, drawables
 (Kotlin apps)               (Java/View apps + Compose bridge)
```

---

## 2. Tokens

### 2.1 Colour — AMOLED first

| Token | AMOLED | Dark | Light | Use |
|---|---|---|---|---|
| `bg` | `#000000` | `#0E0F11` | `#FAFAF8` | App background |
| `surface` | `#0A0A0A` | `#17181B` | `#FFFFFF` | Cards, sheets |
| `surfaceAlt` | `#111111` | `#1F2125` | `#F1F0EC` | Nested rows, chips |
| `border` | `#1E1E1E` | `#2A2C31` | `#E2E0DA` | 1dp hairline (replaces shadows) |
| `text` | `#F2F2F2` | `#ECECEC` | `#15161A` | Primary text |
| `textMuted` | `#9A9A9A` | `#9A9CA1` | `#5F6066` | Secondary, captions |
| `accent` | `#C2664B` | `#C2664B` | `#B0563D` | Terracotta — primary action |
| `accentAlt` | `#E0A32E` | `#E0A32E` | `#B5811C` | Haldi — selected tile, highlight |
| `accentDeep` | `#3D5A98` | `#3D5A98` | `#33497A` | Indigo — links, info |
| `ok` | `#4C8C4A` | `#4C8C4A` | `#3C7A3A` | Granted / clean |
| `warn` | `#C98A28` | `#C98A28` | `#9A6A1C` | Requested / attention |
| `danger` | `#C0473F` | `#C0473F` | `#A33A33` | Revoked / destructive |

Rules:
- On AMOLED, `border` carries all separation. **No elevation shadows** — invisible on `#000000`.
- One accent action per screen.
- **Selected tile** = `accentAlt` at 18% fill + 1dp `accentAlt` border (see the highlighted tile in the store and launcher references). Never a full-opacity fill with white text.
- **Hero cards** (§5.6 Spaces/WorkSpace) may use a *subtle* two-stop gradient of `surfaceAlt` → `accent`/`accentDeep` at 12% opacity. Hero gradients are allowed **only** in Launcher, WorkSpace and the App Store banner — never inside a utility app.
- Contrast ≥ 7:1 for text on `bg`; `textMuted` never carries a value the user must read.

### 2.2 Type

System font only (Roboto / Noto) — no bundled font: costs APK size and breaks Indian-script fallback.

| Token | Size / line | Weight | Use |
|---|---|---|---|
| `display` | 56 / 60 | 300 | Clock face, one number per screen |
| `metric` | 32 / 38 | 400 | "272 Apps", "664 MB", donut centre |
| `title` | 28 / 34 | 400 | Screen title ("Application", "Screen lock") |
| `heading` | 20 / 26 | 500 | Section header ("Large apps", "Favorites") |
| `body` | 16 / 24 | 400 | Rows, paragraphs |
| `label` | 14 / 20 | 500 | Buttons, tabs, chips |
| `caption` | 12 / 16 | 400 | Row sub-label ("5 seconds after timeout") |
| `mono` | 14 / 20 | 400 | Hashes, version codes, log output |

### 2.3 Spacing, radius, motion

- 4dp grid; only **4, 8, 12, 16, 24, 32, 48**.
- Screen padding 16dp · row padding 14dp vertical · card padding 16dp · grid gap 8–12dp.
- Radius: 12dp rows/cards · 16dp sheets · 20dp hero cards · 999dp circular icon buttons.
- Touch target ≥ 48dp. Motion 120ms (state) / 200ms (screen). No bounce, no shimmer.

### 2.4 Iconography

- One 96px SVG per app in `nijatva-design/icons/<app>/`, generated into adaptive foreground/background/monochrome + `mipmap-anydpi-v26`.
- Line-art, 1.5dp stroke, single accent colour, transparent background.
- Monochrome variant is required (themed-icon launchers, and the circular-icon drawer style in the references).
- **Never** put a generated icon inside a coloured circle for in-app lists — circles are for the launcher and store only, where the icon *is* the content.

---

## 3. Components (build once, use 30 times)

| Component | Used by | Notes |
|---|---|---|
| `NijatvaTopBar` | all | Title + optional trailing chip ("Offline"), overflow |
| `PrivacyBanner` | all | `SAF: granted · INTERNET: not requested`; `ok` / `warn` / `danger` |
| `TabBarTop` | store, launcher, drawer | `Explore · Installed · Updates` style, underline indicator |
| `BottomBar` | all | Exactly three destinations: Home, Vault/Local, Settings |
| `ToggleRow` | all | Label + caption + switch, 56dp, whole row tappable |
| `NavRow` | all | Label + caption + chevron |
| `ValueRow` | all | Label + right-aligned value |
| `AppRow` | store, manager, launcher | 56dp icon · name · one-line summary · right-aligned version |
| `StatTripleRow` | store detail, manager | Three cells: Version · Size · Source / Code, divided by hairlines |
| `ChipRow` / `TagChips` | launcher, manager, store | Horizontal favourites; tags with counts (`Tools (24)`) |
| `TileGrid` | launcher, manager | 3–5 column square tiles, label inside or below |
| `CardGrid` | store | 2-column cards: icon, name, summary, action |
| `HeroCard` | launcher, WorkSpace, store banner | Rounded 20dp, optional gradient, title top-left |
| `MetricCard` | manager | Big number + label ("272 Apps / 243 user · 29 system") |
| `BarList` | manager | Ranked rows: label + proportional bar + value (Large apps) |
| `RiskDonut` | manager, store | Donut with Low / Medium / High buckets + centre count |
| `UsageChart` | manager | 7-bar weekly chart, no gridlines, one highlighted bar |
| `ExpandableSection` | about, store detail | Header + chevron + body (Screenshots, Links, Permissions) |
| `PrimaryButton` / `QuietButton` | all | Filled accent / text-only |
| `InstallButton` | store | Full-width, `accent` fill, state machine: Install → Downloading → Verifying → Update |
| `ProgressRow` | store | Names the sha256 verify step — never a bare spinner |
| `SearchField` / `SearchFab` | launcher, store | Rounded 48dp field; circular FAB variant |
| `PermissionRiskBadge` | store, manager | `ok`/`warn`/`danger` dot + word, never colour alone |
| `EmptyState` | all | Icon + one sentence (why) + one action |
| `ConfirmSheet` | all | Destructive action last, `danger`, named ("Delete 3 notes") |

---

## 4. Reference catalogue — all 17 screens mapped

`BUILD` = ship it as drawn (with our tokens). `REFRAME` = the pattern is good, the feature is OS-only or unverifiable, so the label and the data change.

| # | Reference | Nijatva screen | Verdict |
|---|---|---|---|
| 1 | AMOLED home: big clock, date, `Favorites` chips, two circular buttons | Clock home · Launcher home | **BUILD** — `display` token, `ChipRow`, circular shortcuts |
| 2 | App drawer, tabs (`Applications / QR Code Scanner`), 4-col icons, bottom back + search circles | Launcher drawer | **BUILD** |
| 3 | AMOLED search + tile grid, one highlighted tile | Launcher / App Manager search results | **BUILD** — highlight per §2.1 |
| 4 | Store: `Updates` list, "Update all", `Popular apps`, category rows, detail with Install | App Store — Updates + Popular | **BUILD** — "Update all" → "Update 7", progress row names the sha256 step. No charts, no ads slot, no reviews |
| 5 | Privacy dashboard: 24 h donut, per-app camera/mic/location timestamps | — | **REFRAME** → "Permission Audit": *requested* permissions, targetSdk, install source, risk label. Never "used" |
| 6 | Permission manager "17 of 60 apps allowed camera" | App Manager → Permissions | **REFRAME** — show apps that *declare* each permission; tapping deep-links to system settings |
| 7 | Privacy controls, green "Allow only while using" | — | **REFRAME** — OS permission prompt; we show our own state + deep link |
| 8 | Screen lock: scramble PIN, power-button lock, camera-when-locked | Vault / WorkSpace own lock settings | **REFRAME** — our lock only: PIN length, scramble our keypad, auto-lock timeout, biometric |
| 9 | F-Droid "Latest" feed: 2-col cards, 5-tab bottom bar, search FAB | App Store — Latest feed | **BUILD** — 3 tabs (Explore · Installed · Updates), not 5. "Nearby" waits for the transfer feature |
| 10 | Icon-pack picker: large rows with icon + name, tabs Apps/Installed/Updates | `:signature` → Appearance | **BUILD** — icon packs are a launcher feature, offered to every app's Appearance screen |
| 11 | Droid-ify app detail: big title, icon + name + package, `Details`, "Ignore all updates", Version/Size/Source row, Screenshots section | App Store — app detail | **BUILD** — the canonical detail layout. "Ignore updates" is a real local preference |
| 12 | Exodus-style: Rating 4.8, **Privacy 3/10**, "Privacy analyses: Permissions / Trackers", version/updated/licence/requires | App Store — Privacy tab on app detail | **BUILD, differently** — no rating (we have no server). Privacy score computed **at build time by `no-gms-check`** and shipped in the index JSON: banned groups found, dependency count, INTERNET yes/no, permission list. Honest, offline, verifiable |
| 13 | Thunderbird-style: app grid + search, then a sheet with `Links`, `Permissions`, `Versions` expandable sections | `:signature` → About / Developer | **BUILD** — exact three sections: Links (source, issues, licence), Permissions (declared, with "INTERNET: not requested"), Versions (app, core, index) |
| 14 | App Manager dashboard: "272 Apps", New & updated row with timestamps, Tags with counts, Large apps bars, Permissions donut with Low/Medium/High, Usage screen with screen-time bars + launcher counts | App Manager (new app, Phase 4) | **BUILD with limits** — counts, sizes, tags, risk buckets: yes. Screen time / launch counts need `PACKAGE_USAGE_STATS` (special access); label them "approximate, from Android usage stats" and keep them off by default |
| 15 | Spaces: 2-col large gradient cards (Notes, Tasks, Diary, Bookmarks, Calendar, Assistant), bottom nav | Launcher → Spaces · WorkSpace profiles | **BUILD** — `HeroCard`; gradient allowed here only. WorkSpace reuses it for profile cards |
| 16 | App drawer search, circular white-on-black icons, 5-col, localized labels (Czech) | Launcher drawer (alternate style) | **BUILD** — a per-user choice: circular monochrome vs full-colour icons |
| 17 | Neo Store: rows with icon, name, version right-aligned, vertical category lettering, sort/filter chip | App Store — Categories browse | **BUILD** — but replace the vertical lettering with a normal sticky header; vertical text fails at 200% font scale and in RTL |

### 4.1 The one reference we deliberately do not copy

Nothing in the catalogue needs an account, a rating, a review, a download count or a "trending" list. Those numbers need a server that logs users, which is the thing the suite exists to avoid. Where a reference shows them, the Nijatva screen shows a **fact we can prove offline**: version, size, sha256, signer fingerprint, permissions, minSdk, source URL, build date.

---

## 5. Screen specs

### 5.1 Standard app shell (every app)

`TopBar` → `PrivacyBanner` → primary surface → `BottomBar` (Home · Vault/Local · Settings).

### 5.2 App Store — Explore

`TabBarTop` (Explore · Installed · Updates) → `SearchField` → banner `HeroCard` (suite name, "N apps, 0 trackers") → `CardGrid` of apps with one-line summaries → `TagChips` for categories.
Empty `summary` is a policy failure: the current index entry for Photo Editor has an empty `summary` and `description`, and it must not ship that way.

### 5.3 App Store — app detail

```
[ back ]                                    [ share ]
Icon  Nijatva Photo Editor
      com.nijatva.photo.editor · 1.6.0
[ Install / Update ]  (full width, accent)
Version 1.6.0 | Size 6.5 MB | minSdk 26        <- StatTripleRow
[ Privacy ▾ ]  No Google Play Services · 0 banned groups · INTERNET: not requested
[ Permissions ▾ ]  READ_MEDIA_IMAGES, READ/WRITE_EXTERNAL_STORAGE (legacy)
[ Screenshots ▾ ]  3 images
[ Links ▾ ]  Source · Issues · Licence (Apache-2.0)
Description (3 lines + "More")
sha256  bce46bb2…f401c   ·  signer CN=Vasudev Dangaya
```

The sha256 and signer are shown to the user, not hidden in a log. That is the whole pitch.

### 5.4 App Store — Updates

Rows: app icon, name, `1.5.0 → 1.6.0`, size, per-row `Update`. Header button "Update 7". Download shows `ProgressRow` with the step names: *Downloading · Verifying sha256 · Checking signer · Handing to installer*. The system confirmation dialog is described in one caption: "Android will ask you to confirm."

### 5.5 Launcher

- Home: clock (`display`), date, `Favorites` chip row with `Reorder`, search field, two circular shortcuts (phone, camera).
- Drawer: search field, 4–5 column `TileGrid`, toggle between full-colour and circular monochrome icons, A–Z jump list, long-press → app info / uninstall.
- Spaces: `HeroCard` grid (§5.6), each space opens a filtered drawer.
- Permissions: `HOME` role + `QUERY_ALL_PACKAGES`; no privileged access needed.

### 5.6 WorkSpace / Spaces cards

2-column `HeroCard`: title top-left (`heading`), 3D-style icon bottom-right, optional subtitle count ("12 apps"). Tap → profile. Long-press → freeze / unfreeze / rename. Freezing needs `DeviceAdmin` or a shell path — state which one, per profile.

### 5.7 App Manager

- Header `MetricCard`: "272 Apps / 243 user · 29 system".
- `BarList` "Large apps": top 5 by size, tap → per-app detail.
- `RiskDonut` "Permissions": Low / Medium / High by **requested** permission count and category, with a footnote stating the method.
- `TagChips`: category counts, computed from a local rules table (no server classification).
- Per-app detail: name, package, version, size, `StatTripleRow`, storage bar, `UsageChart` (if `PACKAGE_USAGE_STATS` granted), actions `Clear cache` · `Force stop` · `Uninstall` · `App info`, and the Privacy tab from §5.3.
- Every action here is a real Android API call, not a mock. If a call needs special access, the row is disabled with the reason, never faked.

### 5.8 Appearance (in `:signature`, every app)

Theme (AMOLED / Dark / Light / System), accent (terracotta / haldi / indigo), icon pack (launcher only), text size, "disable animations", and the on/off switch for the privacy banner. These live in `core:prefs` once it exists; until then `:signature` stores them in plain preferences and says so.

### 5.9 About / Developer (in `:signature`, every app)

Three `ExpandableSection`s: **Links** (source, issues, licence), **Permissions** (declared list + "INTERNET: not requested"), **Versions** (app, `com.nijatva:signature`, index version, build date, signer fingerprint). Suite counts are read from `APP-REGISTRY.json`, never hardcoded — the current Developer screen says 22 repositories / 28 apps / 14 with code, and the real numbers are 28 / 32 / 17.

---

## 6. Accessibility and language

- Every icon-only button has `contentDescription`; a toggle reads as one unit.
- Contrast ≥ 4.5:1 body, 3:1 large; re-verify after any palette change.
- Tap targets ≥ 48dp even when the visual is 24dp.
- 200% font scale must not clip: rows grow, values never truncate to "…".
- RTL-safe: no hardcoded left/right padding; no vertical text (see reference 17).
- Indian-language strings in `values-<lang>/strings.xml`; numerals international by default with a per-language override.
- No colour-only meaning: "Granted" carries the word, not just green.

---

## 7. Do / Don't

| Do | Don't |
|---|---|
| One accent action per screen | Two filled buttons fighting |
| Hairline borders on AMOLED | Shadows on pure black |
| Show the permission truth on screen | Bury it in Settings → About |
| Name the verify step in a download | Bare spinner, then "Install" |
| Ship the build-time privacy report in the index | Copy a "Privacy 3/10" score you cannot compute |
| Label usage numbers "approximate, from Android usage stats" | Present OS-level access history as your own data |
| Grow rows for large font | Truncate a value with "…" |
| One token source for Java and Compose | A Compose-only theme six apps cannot use |
| Say "requested permission" | Say "used camera 6 times" when the app cannot know |

---

## 8. Build order for UI

| Order | What | Why now |
|---|---|---|
| 1 | Tokens (`tokens.json` → `colors.xml`/`dimens.xml` + Compose theme) | Everything else depends on it; unblocks Java apps too |
| 2 | `TopBar`, `PrivacyBanner`, `ToggleRow`, `NavRow`, `ValueRow`, `EmptyState`, `PrimaryButton`, `BottomBar` | The shell of all 30 apps |
| 3 | About/Developer (`ExpandableSection` ×3) | Every app needs it; it also carries the honest numbers |
| 4 | Store: app detail → Updates → Explore (`StatTripleRow`, `InstallButton`, `ProgressRow`, `AppRow`, `CardGrid`) | Phase 0.1's visible half |
| 5 | Launcher drawer + search (`TileGrid`, `SearchField`) | Reuses the icon system immediately |
| 6 | App Manager (`MetricCard`, `BarList`, `RiskDonut`) | Phase 4, but it is the best showcase of the suite's promise |
| 7 | Spaces / WorkSpace `HeroCard` | After `core:prefs` exists |

Screens marked **REFRAME** in §4 are not built at all until the label can be honest.

---

*Tokens are code. `nijatva-design` holds sources and generated resources; `core:design` holds the Compose implementation. Change a token once and both halves of the suite move together.*
