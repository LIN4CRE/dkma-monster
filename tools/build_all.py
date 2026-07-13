#!/usr/bin/env python3
# =============================================================================
#  DKMA MONSTER  --  Single-source build orchestrator
#  Regenerates every artifact derived from data/oem_registry.json:
#    * android/DkmaRegistry.kt   (in-app library registry)
#    * web/site/                 (self-hostable dashboard)
#
#  Usage:  python3 tools/build_all.py           # regenerate everything
#          python3 tools/build_all.py --check    # verify nothing is stale (CI)
# =============================================================================
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REGISTRY = os.path.join(ROOT, "data", "oem_registry.json")


def run(cmd):
    print("  $", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT).returncode


def validate_registry():
    """Structural sanity on the JSON before generating from it."""
    with open(REGISTRY, encoding="utf-8") as f:
        reg = json.load(f)
    ids = set()
    problems = []
    for o in reg["oems"]:
        if o["id"] in ids:
            problems.append(f"duplicate OEM id: {o['id']}")
        ids.add(o["id"])
        if not o.get("steps"):
            problems.append(f"{o['id']}: no steps")
        for s in o["steps"]:
            has = ("components" in s) or ("use" in s)
            if not has:
                problems.append(f"{o['id']}/{s.get('id')}: no components or use")
            for c in s.get("components", []):
                if "/" not in c:
                    problems.append(f"{o['id']}/{s['id']}: bad component '{c}'")
    if problems:
        print("Registry validation FAILED:")
        for p in problems:
            print("  -", p)
        return False
    print(f"Registry OK: {len(reg['oems'])} OEMs, "
          f"{sum(len(o['steps']) for o in reg['oems'])} steps.")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify generated artifacts are up to date (CI mode)")
    args = ap.parse_args()

    print("== Validate registry ==")
    if not validate_registry():
        return 1

    gen = os.path.join("tools", "gen_kotlin_registry.py")
    gen_kmp = os.path.join("tools", "gen_kmp_registry.py")

    if args.check:
        print("== Check Android Kotlin registry drift ==")
        rc = run([sys.executable, gen, "--check"])
        if rc != 0:
            return rc
        print("== Check KMP registry drift ==")
        rc = run([sys.executable, gen_kmp, "--check"])
        if rc != 0:
            return rc
        print("== (web site is regenerated on demand; not drift-checked) ==")
        print("\nAll single-source checks passed.")
        return 0

    print("== Generate Android Kotlin registry ==")
    if run([sys.executable, gen]) != 0:
        return 1

    print("== Generate KMP registry ==")
    if run([sys.executable, gen_kmp]) != 0:
        return 1

    print("== Generate web dashboard ==")
    if run([sys.executable, os.path.join("web", "build.py")]) != 0:
        return 1

    print("\nDone. All artifacts regenerated from data/oem_registry.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
