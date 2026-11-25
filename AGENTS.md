# AGENTS.md — instructions for any coding agent working on Nijatva

Read `docs/MASTER-ARCHITECTURE.md` first. It carries the verified state and the platform limits.

## Ground rules

1. **Facts come from the repositories, not from READMEs.** If you have not read the file, say "unverified".
2. **Never suggest** Firebase, AdMob, Crashlytics, Play Core, Play-variant ML Kit, Google Maps SDK,
   FusedLocationProvider, Google Sign-In, `MANAGE_EXTERNAL_STORAGE`, `androidx.security:security-crypto`,
   NanoHTTPD, or any sync/cloud feature.
3. **Never suggest** committing a binary (AAR/APK/JAR) or a keystore to git.
4. **Repo ≠ release ≠ indexed.** Done = signed release + index entry + installs and updates on a phone.
5. One PR = one concern. No drive-by refactors.
6. When asked "can you do X", answer in four lines: verdict (HAAN / NAHI / PARTIAL) · what is needed ·
   risk or blocker · exact next step.
7. If a premise is wrong, correct it first, then answer.

## Sources of truth

| Question | File |
|---|---|
| Which apps exist, and their status | `docs/APP-REGISTRY.json` |
| What the ecosystem is, and what a normal app cannot do | `docs/MASTER-ARCHITECTURE.md` |
| What to build next | `docs/DEVELOPMENT-ROADMAP.md` |
| Privacy, permissions, banned dependencies | `docs/SECURITY-POLICY.md` |
| Signing, tagging, index rules | `docs/RELEASE-POLICY.md` |
| Colour, type, components, screen specs | `docs/DESIGN-SYSTEM.md` |

## Before answering anything factual

```
gh repo list nijatva --limit 100
git ls-files | grep -Ei '\.(aar|apk|jar|jks|keystore)$'      # must print nothing
grep -rEi 'com.google.android.gms|firebase|play-services|admob|crashlytics' --include='*.gradle*' .
python3 ../nijatva-core/tools/gen_apps_json.py --check        # apps.json must not be stale
```

State in five lines: what is real, what is claimed but not real, and the single blocking gap.

## Environment limits

An agent sandbox typically has Python, git and `gh`, but **no Java, Gradle, Android SDK or apksigner**.
You can read, audit, write code, generate the index and review. You cannot build or sign an APK,
install on a device, or publish a release. Say so instead of pretending.
