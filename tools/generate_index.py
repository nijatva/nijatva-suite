#!/usr/bin/env python3
"""
Nijatva suite index generator.

Builds ``index-v1.json`` for the self-hosted Nijatva repository out of GitHub
Releases, and refuses to index any APK that breaks a promise the suite makes to
its users.

Two things this file is careful about:

1. **It checks the shipped artifact, not the build file.** ``no-gms-check`` runs
   at build time on a classpath. This runs on the finished APK and reads the
   actual dex. An app that passes the build check but ships a banned SDK is
   caught here, before a user can download it.

2. **It is free and silent.** No network calls except the GitHub API and the
   release assets themselves. No telemetry, no token required, no service to
   pay for. Unauthenticated GitHub API is 60 requests an hour, which is more
   than enough for a suite of 24 apps.

Promises enforced (see ``tools/index-policy.json`` to tune):

* no Play Services, Firebase, advertising, billing or crypto-mining code
* not a debug build
* no ``MANAGE_EXTERNAL_STORAGE`` — the suite uses SAF
* signing certificate pinned per app, once you record it
* ``versionCode`` only ever goes up, so an update is always an update

Usage::

    python3 tools/generate_index.py --apps core/tools/apps.json \\
        --out index-v1.json

Exit codes: 0 written, 1 a gate failed, 2 environment problem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

API = "https://api.github.com"
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
USER_AGENT = "Nijatva-Index-Generator/1"

# ---------------------------------------------------------------------------
# Defaults. The policy file may narrow these; it may not remove a category.
# ---------------------------------------------------------------------------

BANNED_DEX: dict[str, list[str]] = {
    "play services": ["com/google/android/gms", "com/google/firebase",
                      "com/google/android/play"],
    "advertising": ["com/google/android/gms/ads", "com/applovin",
                    "com/facebook/ads", "com/unity3d/ads", "com/ironsource",
                    "com/vungle", "com/chartboost", "com/mopub",
                    "com/mintegral", "com/startapp", "com/tapjoy",
                    "com/inmobi", "com/adcolony"],
    "billing": ["com/android/billingclient", "com/android/vending/billing"],
    "crypto mining": ["coinhive", "cryptonight", "xmrig", "minergate",
                      "coinimp", "deepminer", "jsecoin", "cryptoloot",
                      "webminepool", "crypto-loot"],
    "tracking": ["com/crashlytics", "com/amplitude", "com/mixpanel",
                 "com/segment/analytics", "com/appsflyer", "com/adjust/sdk",
                 "com/flurry"],
}

FORBIDDEN_PERMISSIONS = {
    "android.permission.MANAGE_EXTERNAL_STORAGE":
        "the suite uses Storage Access Framework, not all-files access",
    "com.android.vending.BILLING":
        "the suite has no paid anything",
}

DEFAULT_POLICY: dict[str, Any] = {
    "minTargetSdk": 34,
    "requireReleaseTag": True,
    "allowDexScanOff": False,
    "apps": {},
}

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


class GateError(Exception):
    """A promise was broken by an artifact. Never caught silently."""


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def gh_json(url: str, token: str | None) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def gh_download(url: str, token: str | None, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              check=True).stdout
    except FileNotFoundError:
        raise GateError(f"missing tool: {cmd[0]}")
    except subprocess.CalledProcessError as e:
        raise GateError(f"{' '.join(cmd)} failed: {e.stderr.strip()[:400]}")


# ---------------------------------------------------------------------------
# APK inspection
# ---------------------------------------------------------------------------


def find_build_tool(name: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk:
        bt = Path(sdk) / "build-tools"
        if bt.is_dir():
            for version in sorted(bt.iterdir(), reverse=True):
                candidate = version / name
                if candidate.is_file():
                    return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise GateError(f"{name} not found; pass --aapt2/--apksigner or install build-tools")


def read_badging(apk: Path, aapt2: str) -> dict[str, Any]:
    """Parse `aapt2 dump badging` into the few fields the index needs."""
    out = run([aapt2, "dump", "badging", str(apk)])
    info: dict[str, Any] = {"permissions": [], "nativeCode": [], "debuggable": False}

    m = re.search(r"package: name='([^']*)' versionCode='([^']*)' versionName='([^']*)'", out)
    if not m:
        raise GateError(f"{apk.name}: aapt2 could not read the package block")
    info["packageName"] = m.group(1)
    info["versionCode"] = int(m.group(2))
    info["versionName"] = m.group(3) or str(info["versionCode"])

    for key, field in (("sdkVersion", "minSdkVersion"), ("targetSdkVersion", "targetSdkVersion")):
        mm = re.search(rf"{key}:'(\d+)'", out)
        if mm:
            info[field] = int(mm.group(1))

    info["debuggable"] = "application-debuggable" in out

    for perm in re.finditer(r"uses-permission: name='([^']+)'", out):
        info["permissions"].append(perm.group(1))

    nc = re.search(r"native-code: (.+)", out)
    if nc:
        info["nativeCode"] = re.findall(r"'([^']+)'", nc.group(1))

    return info


def read_cert(apk: Path, apksigner: str) -> dict[str, str]:
    out = run([apksigner, "verify", "--print-certs", str(apk)])
    sha256 = re.search(r"certificate SHA-256 digest: ([0-9a-fA-F]+)", out)
    if not sha256:
        raise GateError(f"{apk.name}: unsigned or unreadable signing certificate")
    dn = re.search(r"certificate DN: (.+)", out)
    return {"sig": sha256.group(1).lower(), "signer": (dn.group(1).strip() if dn else "")}


def dex_hits(apk: Path, needles: list[str]) -> set[str]:
    """Return the needles that appear in any classes*.dex of the APK.

    A dex string table stores ASCII contiguously, so a byte search over the dex
    is a reliable detector of a package prefix without needing a dex parser.
    """
    found: set[str] = set()
    with zipfile.ZipFile(apk) as z:
        for name in z.namelist():
            if re.fullmatch(r"classes\d*\.dex", name):
                blob = z.read(name)
                for needle in needles:
                    if needle.encode() in blob:
                        found.add(needle)
    return found


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def gate(meta: dict[str, Any], cert: dict[str, str], hits: set[str],
         policy: dict[str, Any], app_policy: dict[str, Any],
         previous: dict[str, Any] | None) -> list[str]:
    """Return a list of human-readable violations. Empty means it ships."""
    bad: list[str] = []
    pkg = meta["packageName"]

    if meta["debuggable"]:
        bad.append("debug build (application-debuggable) — assemble a signed release")

    min_target = int(policy.get("minTargetSdk", DEFAULT_POLICY["minTargetSdk"]))
    if meta.get("targetSdkVersion", 0) < min_target:
        bad.append(f"targetSdkVersion {meta.get('targetSdkVersion')} < {min_target}")

    for perm, why in FORBIDDEN_PERMISSIONS.items():
        if perm in meta["permissions"]:
            bad.append(f"declares {perm} — {why}")

    if hits and not app_policy.get("allowDexScanOff", policy.get("allowDexScanOff", False)):
        for needle in sorted(hits):
            bad.append(f"contains banned code: {needle}")

    pinned = app_policy.get("signingSha256")
    if pinned and pinned.lower() != cert["sig"]:
        bad.append(f"signing certificate changed: index pins {pinned}, APK is {cert['sig']}")

    if previous and meta["versionCode"] <= previous["versionCode"]:
        bad.append(f"versionCode {meta['versionCode']} is not above the published "
                   f"{previous['versionCode']}")

    if bad:
        log(f"  ✗ {pkg} {meta['versionName']} ({meta['versionCode']})")
        for line in bad:
            log(f"      {line}")
    return bad


# ---------------------------------------------------------------------------
# Release selection
# ---------------------------------------------------------------------------


def iter_releases(owner: str, repo: str, token: str | None) -> list[dict[str, Any]]:
    """apps.json stores the repository name only, so the owner is added here."""
    releases: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = gh_json(f"{API}/repos/{owner}/{repo}/releases?per_page=100&page={page}", token)
        if not batch:
            return releases
        releases.extend(batch)
        if len(batch) < 100:
            return releases
        page += 1


def pick_apk(release: dict[str, Any]) -> dict[str, Any] | None:
    apks = [a for a in release.get("assets", []) if a["name"].lower().endswith(".apk")]
    if not apks:
        return None
    # One APK per release is the suite rule. If a release carries several,
    # prefer a universal build, otherwise refuse rather than guess.
    if len(apks) > 1:
        universal = [a for a in apks if "universal" in a["name"].lower()]
        if len(universal) == 1:
            return universal[0]
        raise GateError(f"{release['tag_name']}: {len(apks)} APKs attached; "
                        f"attach exactly one (or mark one 'universal')")
    return apks[0]


# ---------------------------------------------------------------------------
# Index assembly
# ---------------------------------------------------------------------------


def build_repo_block(address: str, name: str, description: str) -> dict[str, Any]:
    return {
        "timestamp": int(time.time() * 1000),
        "version": 1,
        "name": name,
        "address": address,
        "description": description,
        "maxAge": 0,
    }


def package_entry(meta: dict[str, Any], cert: dict[str, str], apk: Path,
                  digest: str, url: str, added: int) -> dict[str, Any]:
    return {
        "apkName": f"{meta['packageName']}_{meta['versionCode']}.apk",
        "apkUrl": url,                     # Nijatva client uses this
        "hash": digest,
        "hashType": "sha256",
        "size": apk.stat().st_size,
        "packageName": meta["packageName"],
        "versionCode": meta["versionCode"],
        "versionName": meta["versionName"],
        "sig": cert["sig"],
        "signer": cert["signer"],
        "minSdkVersion": meta.get("minSdkVersion", 0),
        "targetSdkVersion": meta.get("targetSdkVersion", 0),
        "nativecode": meta.get("nativeCode", []),
        "uses-permission": [{"name": p} for p in meta["permissions"]],
        "added": added,
    }


def app_entry(app: dict[str, Any], pkg: str, newest: dict[str, Any],
              owner: str = "nijatva") -> dict[str, Any]:
    name = app.get("name") or pkg
    summary = app.get("summary") or ""
    return {
        "packageName": pkg,
        "name": name,
        "summary": summary,
        "license": app.get("license", "Apache-2.0"),
        "sourceCode": f"https://github.com/{owner}/{app['repo']}" if app.get("repo") else "",
        "issueTracker": f"https://github.com/{owner}/{app['repo']}/issues" if app.get("repo") else "",
        "categories": app.get("categories", []),
        "suggestedVersionCode": newest["versionCode"],
        "suggestedVersionName": newest["versionName"],
        "localized": {"en-US": {"name": name, "summary": summary,
                                "description": app.get("description", summary)}},
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def load_policy(path: Path | None) -> dict[str, Any]:
    policy = json.loads(json.dumps(DEFAULT_POLICY))
    if path and path.is_file():
        user = json.loads(path.read_text())
        policy["minTargetSdk"] = user.get("minTargetSdk", policy["minTargetSdk"])
        policy["apps"] = user.get("apps", {})
        # Categories may be extended, never deleted.
        for category, needles in user.get("extraBannedDex", {}).items():
            policy.setdefault("extraBannedDex", {})[category] = needles
    return policy


def all_needles(policy: dict[str, Any]) -> list[str]:
    needles = [n for group in BANNED_DEX.values() for n in group]
    for group in policy.get("extraBannedDex", {}).values():
        needles.extend(group)
    return needles


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the Nijatva index-v1.json")
    ap.add_argument("--apps", required=True, help="path to apps.json (from nijatva-core)")
    ap.add_argument("--owner", default="nijatva",
                    help="GitHub organisation that owns the app repositories")
    ap.add_argument("--out", default="index-v1.json")
    ap.add_argument("--policy", default="tools/index-policy.json")
    ap.add_argument("--previous", default=None,
                    help="existing index-v1.json, used for versionCode ordering")
    ap.add_argument("--address", default="https://nijatva.github.io/nijatva-suite")
    ap.add_argument("--name", default="Nijatva")
    ap.add_argument("--description", default="Local-first Android apps. No Google Play Services.")
    ap.add_argument("--aapt2", default=None)
    ap.add_argument("--apksigner", default=None)
    ap.add_argument("--token", default=os.environ.get("SUITE_INDEX_TOKEN"))
    ap.add_argument("--dry-run", action="store_true", help="check everything, write nothing")
    args = ap.parse_args(argv)

    policy = load_policy(Path(args.policy))
    needles = all_needles(policy)
    apps = json.loads(Path(args.apps).read_text())["apps"]

    previous: dict[str, Any] = {}
    if args.previous and Path(args.previous).is_file():
        previous = json.loads(Path(args.previous).read_text()).get("packages", {})

    aapt2 = find_build_tool("aapt2", args.aapt2)
    apksigner = find_build_tool("apksigner", args.apksigner)

    packages: dict[str, list[dict[str, Any]]] = {}
    app_meta: dict[str, dict[str, Any]] = {}
    violations: list[str] = []
    workdir = Path(tempfile.mkdtemp(prefix="nijatva-index-"))

    try:
        for app in apps:
            repo = app.get("repo")
            if not repo:
                continue
            log(f"{repo}")
            try:
                releases = iter_releases(args.owner, repo, args.token)
            except urllib.error.HTTPError as e:
                violations.append(f"{repo}: GitHub returned {e.code}")
                continue

            for release in releases:
                if release.get("draft"):
                    continue
                tag = release.get("tag_name", "")
                if policy.get("requireReleaseTag", True) and not SEMVER.match(tag):
                    log(f"  – skip {tag or '(no tag)'}: not a version tag")
                    continue
                try:
                    asset = pick_apk(release)
                except GateError as e:
                    violations.append(str(e))
                    continue
                if not asset:
                    continue

                local = workdir / f"{repo}-{tag}.apk"
                gh_download(asset["browser_download_url"], args.token, local)
                digest = sha256_file(local)

                try:
                    meta = read_badging(local, aapt2)
                    cert = read_cert(local, apksigner)
                except GateError as e:
                    violations.append(f"{repo} {tag}: {e}")
                    continue

                app_policy = policy.get("apps", {}).get(meta["packageName"], {})
                hits = dex_hits(local, needles)
                prev = (previous.get(meta["packageName"]) or [None])[0]
                bad = gate(meta, cert, hits, policy, app_policy, prev)
                if bad:
                    violations.extend(f"{meta['packageName']} {tag}: {b}" for b in bad)
                    continue

                entry = package_entry(meta, cert, local, digest,
                                      asset["browser_download_url"],
                                      int(time.mktime(time.strptime(
                                          release["published_at"][:19], "%Y-%m-%dT%H:%M:%S"))))
                packages.setdefault(meta["packageName"], []).append(entry)
                app_meta.setdefault(meta["packageName"], app)
                log(f"  ✓ {meta['versionName']} ({meta['versionCode']}) {digest[:12]}…")

        if violations:
            log("")
            log(f"{len(violations)} artifact(s) refused:")
            for v in violations:
                log(f"  • {v}")
            if args.dry_run:
                return 1

        for versions in packages.values():
            versions.sort(key=lambda p: p["versionCode"], reverse=True)

        index = {
            "repo": build_repo_block(args.address, args.name, args.description),
            "apps": [app_entry(app_meta[pkg], pkg, versions[0], args.owner)
                     for pkg, versions in sorted(packages.items())],
            "packages": {pkg: versions for pkg, versions in sorted(packages.items())},
        }

        if args.dry_run:
            log(f"dry run: {len(packages)} package(s) would be indexed")
            return 1 if violations else 0

        if violations:
            log("refusing to write an index that skips an app; fix the artifacts above")
            return 1

        Path(args.out).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
        log(f"wrote {args.out}: {len(packages)} package(s), "
            f"{sum(len(v) for v in packages.values())} version(s)")
        return 0
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GateError as e:
        log(f"error: {e}")
        sys.exit(2)
