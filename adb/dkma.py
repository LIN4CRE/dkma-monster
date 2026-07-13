#!/usr/bin/env python3
# =============================================================================
#  DKMA MONSTER  —  Universal "Don't Kill My App!" installer (ADB edition)
#  Cross-platform (Windows / macOS / Linux). One file. Detects the OEM and
#  drives the correct keep-alive settings for ~15 vendor families.
#
#  Grants everything ADB can grant automatically, then opens each vendor's
#  hidden autostart/battery screens in sequence for one-tap confirmation.
#
#  Usage:
#     python3 dkma.py com.your.app              # classic guided run (verifies each step)
#     python3 dkma.py com.your.app --tui        # interactive checklist (arrows)
#     python3 dkma.py com.your.app --auto       # grants only; skip manual pauses
#
#  Per-step verification: after each step, the tool re-reads device state (Doze
#  whitelist, appops, standby bucket) to PROVE whether it took effect. Steps with
#  no readable API are honestly marked "unverifiable" (confirm manually).
#     python3 dkma.py com.your.app --dry-run    # print commands, execute nothing
#     python3 dkma.py com.your.app --json       # machine-readable output
#     python3 dkma.py com.your.app --serial R58...   # target a device
#     python3 dkma.py --list                    # list connected devices
#
#  Exit codes: 0 ok · 1 usage/device error · 2 adb missing · 3 partial failures
#  Requires: adb on PATH, USB debugging enabled. Registry: ../data/oem_registry.json
# =============================================================================
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "..", "data", "oem_registry.json")

EXIT_OK, EXIT_USAGE, EXIT_NOADB, EXIT_PARTIAL = 0, 1, 2, 3

# ---------- pretty ----------------------------------------------------------
_TTY = sys.stdout.isatty()
_QUIET = False  # suppressed in --json mode
def _c(code, s): return f"\033[{code}m{s}\033[0m" if _TTY else s
def bold(s):  return _c("1", s)
def green(s): return _c("32", s)
def yellow(s):return _c("33", s)
def red(s):   return _c("31", s)
def cyan(s):  return _c("36", s)
def dim(s):   return _c("2", s)

def _p(*a, **k):
    if not _QUIET: print(*a, **k)
def step(s): _p("\n" + bold(cyan("==> ")) + bold(s))
def ok(s):   _p("  " + green("\u2713") + " " + s)
def warn(s): _p("  " + yellow("!") + " " + s)
def fail(s): _p("  " + red("\u2717") + " " + s)
def info(s): _p("  " + dim(s))

BANNER = r"""
  ____  _  ____  __    __        __  __  ___  _   _ ____ _____ _____ ____
 |  _ \| |/ /  \/  |  /  \      |  \/  |/ _ \| \ | / ___|_   _| ____|  _ \
 | | | | ' /| |\/| | / /\ \     | |\/| | | | |  \| \___ \ | | |  _| | |_) |
 | |_| | . \| |  | |/ ____ \    | |  | | |_| | |\  |___) || | | |___|  _ <
 |____/|_|\_\_|  |_/_/    \_\   |_|  |_|\___/|_| \_|____/ |_| |_____|_| \_\
        Universal Don't-Kill-My-App installer  .  ADB edition
"""

# ---------- adb helpers -----------------------------------------------------
class Adb:
    """Wraps adb. In dry_run mode, mutating shell commands are recorded, not run.
    Read-only commands (getprop, get-state, list) still run so detection works."""
    READONLY_PREFIXES = (
        ("getprop",), ("pm", "list"), ("am", "get-standby-bucket"),
        ("cmd", "appops", "get"), ("appops", "get"),  # appop reads (verification)
        ("dumpsys", "deviceidle", "whitelist"),  # bare form (no +pkg) is read-only
    )

    def __init__(self, serial=None, dry_run=False):
        self.serial = serial
        self.dry_run = dry_run
        self.commands = []  # recorded (for dry-run / json)

    def _base(self):
        cmd = ["adb"]
        if self.serial:
            cmd += ["-s", self.serial]
        return cmd

    def _is_readonly(self, shell_args):
        if shell_args[:3] == ["dumpsys", "deviceidle", "whitelist"] and len(shell_args) > 3:
            return False  # whitelist +pkg mutates
        for pref in self.READONLY_PREFIXES:
            if tuple(shell_args[:len(pref)]) == pref:
                return True
        return False

    def raw(self, args, timeout=20):
        try:
            r = subprocess.run(self._base() + args, capture_output=True,
                               text=True, timeout=timeout)
            return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
        except FileNotFoundError:
            if not _QUIET:
                fail("adb not found on PATH. Install Android platform-tools.")
                print("     https://developer.android.com/tools/releases/platform-tools")
            sys.exit(EXIT_NOADB)
        except subprocess.TimeoutExpired:
            return 124, "", "timeout"

    def shell(self, args, timeout=20):
        if isinstance(args, str):
            args = args.split()
        printable = "adb shell " + " ".join(args)
        if self.dry_run and not self._is_readonly(args):
            self.commands.append(printable)
            return 0, "", ""  # pretend success
        return self.raw(["shell"] + args, timeout=timeout)

    def getprop(self, key):
        _, out, _ = self.shell(["getprop", key])
        return out.strip()

    def ok_shell(self, args):
        rc, _, _ = self.shell(args)
        return rc == 0

def list_devices():
    _, out, _ = Adb().raw(["devices", "-l"])
    devs = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devs.append(parts[0])
    return devs

# ---------- registry --------------------------------------------------------
def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)

def resolve_ref(reg, ref, pkg):
    section, key = ref.split(".", 1)
    entry = dict(reg[section][key])
    if "data" in entry:
        entry["data"] = entry["data"].replace("%PKG%", pkg)
    return entry

def detect_oem(reg, manuf, brand, props):
    manuf = (manuf or "").lower()
    brand = (brand or "").lower()
    for oem in reg["oems"]:
        m = oem["match"]
        if any(x in manuf for x in m.get("manufacturer", [])): return oem
        if any(x in brand for x in m.get("brand", [])):        return oem
        for p in m.get("props", []):
            if props.get(p):                                   return oem
    return None

# ---------- intent opening --------------------------------------------------
def open_component(adb, comp, extras=None, pkg=None):
    args = ["am", "start", "-n", comp]
    if extras:
        for k, v in extras.items():
            args += ["--es", k, (v or "").replace("%PKG%", pkg or "")]
    return adb.ok_shell(args)

def open_intent(adb, intent, pkg):
    args = ["am", "start"]
    if "action" in intent: args += ["-a", intent["action"]]
    if "component" in intent: args += ["-n", intent["component"]]
    if "data" in intent: args += ["-d", intent["data"].replace("%PKG%", pkg)]
    return adb.ok_shell(args)

def open_step_intent(adb, reg, step_def, pkg):
    """Try components then 'use' ref then app_details. Returns (opened, detail)."""
    if "components" in step_def:
        for comp in step_def["components"]:
            if open_component(adb, comp, step_def.get("extras"), pkg):
                return True, comp.split("/")[-1]
    if "use" in step_def:
        if open_intent(adb, resolve_ref(reg, step_def["use"], pkg), pkg):
            return True, step_def["use"]
    if open_intent(adb, resolve_ref(reg, "generic.app_details", pkg), pkg):
        return True, "generic.app_details (fallback)"
    return False, None

# ---------- grant phase (universal) -----------------------------------------
def grant_phase(adb, pkg):
    """Returns list of {name, ok, cmd} result dicts."""
    results = []
    def rec(name, args):
        cmd = "adb shell " + " ".join(args)
        good = adb.ok_shell(args)
        results.append({"name": name, "ok": good, "cmd": cmd})
        return good

    rec("doze_whitelist", ["dumpsys", "deviceidle", "whitelist", "+" + pkg])
    rec("standby_active", ["am", "set-standby-bucket", pkg, "active"])
    for op in ["RUN_IN_BACKGROUND", "RUN_ANY_IN_BACKGROUND", "START_FOREGROUND"]:
        rec(f"appop_{op}", ["cmd", "appops", "set", pkg, op, "allow"])
    for op in ["AUTO_START", "BOOT_COMPLETED"]:
        rec(f"appop_{op}", ["cmd", "appops", "set", pkg, op, "allow"])
    rec("launch_once", ["monkey", "-p", pkg, "-c",
                        "android.intent.category.LAUNCHER", "1"])
    return results

def verify_phase(adb, pkg):
    out = {}
    _, wl, _ = adb.shell(["dumpsys", "deviceidle", "whitelist"])
    out["in_doze_whitelist"] = pkg in wl
    _, bucket, _ = adb.shell(["am", "get-standby-bucket", pkg])
    out["standby_bucket"] = bucket or None
    return out

# ---------- per-step verification -------------------------------------------
# What each step id can be PROVEN with (where an API exists). Steps not listed
# have no readable state on stock Android -> honestly reported "unverifiable".
VERIFY_MAP = {
    "battery_opt":     [{"kind": "doze"}],
    "recent_lock":     [{"kind": "doze"}],
    "stamina":         [{"kind": "doze"}],
    "app_details":     [{"kind": "appop", "op": "RUN_ANY_IN_BACKGROUND", "want": "allow"},
                        {"kind": "bucket", "want": ["active", "working_set"]}],
    "autostart":       [{"kind": "appop", "op": "AUTO_START", "want": "allow"}],
}

def _appop_state(adb, pkg, op):
    """Return the appop mode string (allow/deny/default/ignore) or None."""
    for cmd in (["cmd", "appops", "get", pkg, op], ["appops", "get", pkg, op]):
        rc, out, _ = adb.shell(cmd)
        if rc == 0 and out:
            # formats: "OP: allow" or "OP: allow; time=..." or "No operations."
            m = re.search(r':\s*([a-zA-Z_]+)', out)
            if m:
                return m.group(1).lower()
            low = out.strip().lower()
            if low in ("allow", "deny", "default", "ignore"):
                return low
    return None

def verify_step(adb, pkg, step_def):
    """Re-read device state to prove whether a step took effect.
    Returns {status, verifiable, checks:[{name, ok, detail}]}.
    status is one of: verified | not_yet | unverifiable."""
    checks = VERIFY_MAP.get(step_def.get("id"))
    if not checks:
        return {"status": "unverifiable", "verifiable": False, "checks": []}

    results = []
    for c in checks:
        if c["kind"] == "doze":
            _, wl, _ = adb.shell(["dumpsys", "deviceidle", "whitelist"])
            good = pkg in wl
            results.append({"name": "battery-optimization exemption",
                            "ok": good,
                            "detail": "in Doze whitelist" if good
                                      else "not in Doze whitelist yet"})
        elif c["kind"] == "appop":
            state = _appop_state(adb, pkg, c["op"])
            good = state == c["want"]
            results.append({"name": f"appop {c['op']}",
                            "ok": good,
                            "detail": f"= {state or 'unknown'}"
                                      f" (want {c['want']})"})
        elif c["kind"] == "bucket":
            _, b, _ = adb.shell(["am", "get-standby-bucket", pkg])
            b = (b or "").strip().lower()
            good = b in [w.lower() for w in c["want"]]
            results.append({"name": "standby bucket",
                            "ok": good,
                            "detail": f"= {b or 'unknown'}"})
    all_ok = all(r["ok"] for r in results) if results else False
    return {"status": "verified" if all_ok else "not_yet",
            "verifiable": True, "checks": results}

def report_step_verify(v):
    """Print a per-step verification result to the console."""
    if not v["verifiable"]:
        info("verify: no readable state on this OEM \u2014 confirm the toggle manually.")
        return
    if v["status"] == "verified":
        ok("verified \u2713  " + "; ".join(c["detail"] for c in v["checks"]))
    else:
        warn("not confirmed yet: " +
             "; ".join(f"{c['name']} {c['detail']}"
                       for c in v["checks"] if not c["ok"]))

def steps_for(reg, oem):
    if oem:
        return oem["steps"]
    return [
        {"id": "battery_opt", "title": "Battery optimization -> Don't optimize",
         "use": "generic.battery_optimization_list"},
        {"id": "app_details", "title": "App info -> Unrestricted",
         "use": "generic.app_details"},
    ]

# ---------- device bring-up (shared) ----------------------------------------
def bring_up(adb, reg, pkg):
    """Connect, detect, validate package. Returns dict of device facts or exits."""
    step("Waiting for device (accept the USB-debugging prompt if shown)...")
    adb.raw(["start-server"])
    adb.raw(["wait-for-device"], timeout=60)
    _, state, _ = adb.raw(["get-state"])
    if state != "device":
        fail(f"Device not ready (state: {state or 'none'}).")
        sys.exit(EXIT_USAGE)
    ok("Device connected.")

    manuf = adb.getprop("ro.product.manufacturer")
    model = adb.getprop("ro.product.model")
    brand = adb.getprop("ro.product.brand")
    android = adb.getprop("ro.build.version.release")
    props = {p: adb.getprop(p) for o in reg["oems"]
             for p in o["match"].get("props", [])}
    ok(f"Device: {manuf} {model}  (Android {android})")

    _, pkgs, _ = adb.shell(["pm", "list", "packages"])
    if f"package:{pkg}" not in pkgs.split():
        fail(f"Package '{pkg}' is not installed on this device. Install it first.")
        sys.exit(EXIT_USAGE)
    ok(f"Target app: {pkg}")

    oem = detect_oem(reg, manuf, brand, props)
    if oem: ok(f"Detected OEM profile: {bold(oem['label'])}")
    else:   warn("Unknown OEM -- using generic (stock Android) profile.")

    return {"manufacturer": manuf, "model": model, "brand": brand,
            "android": android, "oem": oem,
            "oem_id": oem["id"] if oem else "generic",
            "oem_label": oem["label"] if oem else "Generic / Stock Android"}

# ---------- classic (non-TUI) run -------------------------------------------
def run_classic(adb, reg, pkg, facts, auto):
    oem = facts["oem"]
    step("Universal grants (automatic, works on every device)")
    grants = grant_phase(adb, pkg)
    for g in grants:
        (ok if g["ok"] else warn)(
            f"{g['name']} {'= allow/done' if g['ok'] else 'not settable here'}")

    label = facts["oem_label"]
    step(f"Guided vendor steps for {label} "
         f"({'auto/skip' if auto else 'tap Allow each time'})")
    step_results = []
    for sd in steps_for(reg, oem):
        title = sd.get("title", sd.get("id", "setting"))
        step(f"{label} -- {title}")
        opened, detail = open_step_intent(adb, reg, sd, pkg)
        if opened: ok(f"Opened: {detail}")
        else:      fail("Could not open this screen automatically. Open it manually.")
        if not auto and not adb.dry_run:
            try:
                input(yellow("  Adjust the toggle, then press ENTER to verify... "))
            except (EOFError, KeyboardInterrupt):
                print()
        # Per-step live verification: re-read state to prove it took effect.
        v = verify_step(adb, pkg, sd)
        report_step_verify(v)
        step_results.append({"id": sd.get("id"), "title": title,
                             "opened": opened, "detail": detail,
                             "verify": v})

    verify = verify_phase(adb, pkg)
    step("Verification")
    (ok if verify["in_doze_whitelist"] else warn)(
        "Confirmed in Doze whitelist" if verify["in_doze_whitelist"]
        else "Not shown in Doze whitelist (may still be exempt via UI)")
    if verify["standby_bucket"]:
        ok(f"Standby bucket: {verify['standby_bucket']}")

    return grants, step_results, verify

# ---------- interactive TUI (curses; graceful fallback) ---------------------
def run_tui(adb, reg, pkg, facts):
    try:
        import curses
    except Exception:
        info("curses unavailable -- falling back to numbered menu.")
        return run_menu(adb, reg, pkg, facts)

    oem = facts["oem"]
    items = [{"id": s.get("id"), "title": s.get("title", s.get("id")),
              "status": "pending", "detail": None, "verify": None, "def": s}
             for s in steps_for(reg, oem)]
    grants_holder = {"done": False, "results": []}
    verify_holder = {"data": None}

    ICON = {"pending": "[ ]", "opened": "[>]", "done": "[x]",
            "failed": "[!]", "skip": "[-]"}

    def draw(stdscr, sel, msg):
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        title = f" DKMA Monster TUI  .  {facts['oem_label']}  .  {pkg} "
        stdscr.addstr(0, 0, title[:w-1], curses.A_REVERSE)
        stdscr.addstr(2, 2, f"Device: {facts['manufacturer']} {facts['model']} "
                            f"(Android {facts['android']})"[:w-4])
        gstat = "granted" if grants_holder["done"] else "not yet run"
        stdscr.addstr(3, 2, f"Universal grants: {gstat}"[:w-4])

        stdscr.addstr(5, 2, "Steps:"[:w-4])
        row = 6
        for i, it in enumerate(items):
            marker = "->" if i == sel else "  "
            line = f" {marker} {ICON.get(it['status'],'[ ]')} {it['title']}"
            attr = curses.A_BOLD if i == sel else curses.A_NORMAL
            stdscr.addstr(row, 2, line[:w-4], attr)
            row += 1

        help1 = "UP/DOWN move   ENTER open step   c check step   SPACE mark done   s skip"
        help2 = "g run grants   v verify all   a run all remaining   q finish"
        stdscr.addstr(h-4, 2, help1[:w-4], curses.A_DIM)
        stdscr.addstr(h-3, 2, help2[:w-4], curses.A_DIM)
        if msg:
            stdscr.addstr(h-2, 2, msg[:w-4], curses.A_BOLD)
        stdscr.refresh()

    def do_grants():
        grants_holder["results"] = grant_phase(adb, pkg)
        grants_holder["done"] = True
        good = sum(1 for g in grants_holder["results"] if g["ok"])
        return f"Grants applied: {good}/{len(grants_holder['results'])} ok"

    def do_open(it):
        opened, detail = open_step_intent(adb, reg, it["def"], pkg)
        it["detail"] = detail
        it["status"] = "opened" if opened else "failed"
        return (f"Opened: {detail}" if opened
                else "Could not open -- open it manually on the phone")

    def do_check(it):
        """Per-step live verification of the currently-selected step."""
        v = verify_step(adb, pkg, it["def"])
        it["verify"] = v
        if not v["verifiable"]:
            return "Not verifiable via API \u2014 confirm the toggle manually, then press SPACE."
        if v["status"] == "verified":
            it["status"] = "done"
            return "Verified \u2713  " + "; ".join(c["detail"] for c in v["checks"])
        return "Not confirmed yet: " + "; ".join(
            f"{c['name']} {c['detail']}" for c in v["checks"] if not c["ok"])

    def do_verify():
        verify_holder["data"] = verify_phase(adb, pkg)
        d = verify_holder["data"]
        return (f"Doze whitelist: {'YES' if d['in_doze_whitelist'] else 'no'}   "
                f"bucket: {d['standby_bucket'] or '?'}")

    def loop(stdscr):
        curses.curs_set(0)
        sel, msg = 0, "Tip: press 'g' first to apply universal grants."
        while True:
            draw(stdscr, sel, msg)
            ch = stdscr.getch()
            if ch in (curses.KEY_UP, ord('k')):
                sel = (sel - 1) % len(items); msg = ""
            elif ch in (curses.KEY_DOWN, ord('j')):
                sel = (sel + 1) % len(items); msg = ""
            elif ch in (curses.KEY_ENTER, 10, 13):
                msg = do_open(items[sel])
            elif ch in (ord('c'), ord('C')):
                msg = do_check(items[sel])
            elif ch == ord(' '):
                items[sel]["status"] = "done"; msg = "Marked done."
                sel = (sel + 1) % len(items)
            elif ch in (ord('s'), ord('S')):
                items[sel]["status"] = "skip"; msg = "Skipped."
                sel = (sel + 1) % len(items)
            elif ch in (ord('g'), ord('G')):
                msg = do_grants()
            elif ch in (ord('v'), ord('V')):
                msg = do_verify()
            elif ch in (ord('a'), ord('A')):
                if not grants_holder["done"]:
                    do_grants()
                for it in items:
                    if it["status"] in ("pending",):
                        do_open(it)
                        do_check(it)
                msg = "Ran grants + opened + verified all pending steps."
            elif ch in (ord('q'), ord('Q'), 27):
                break

    curses.wrapper(loop)

    # Summarize after leaving curses
    if not grants_holder["done"]:
        grants_holder["results"] = []
    if verify_holder["data"] is None:
        verify_holder["data"] = verify_phase(adb, pkg)
    step("TUI session summary")
    for it in items:
        tag = {"done": green("done"), "opened": cyan("opened"),
               "failed": red("failed"), "skip": dim("skipped"),
               "pending": yellow("pending")}.get(it["status"], it["status"])
        _p(f"  {ICON.get(it['status'],'[ ]')} {it['title']}  ({tag})")
    step_results = [{"id": it["id"], "title": it["title"],
                    "status": it["status"], "detail": it["detail"],
                    "verify": it.get("verify")} for it in items]
    return grants_holder["results"], step_results, verify_holder["data"]

# ---------- numbered-menu fallback (no curses, e.g. bare Windows) ------------
def run_menu(adb, reg, pkg, facts):
    oem = facts["oem"]
    items = [{"id": s.get("id"), "title": s.get("title", s.get("id")),
              "status": "pending", "detail": None, "verify": None, "def": s}
             for s in steps_for(reg, oem)]
    grants = []
    while True:
        print("\n" + bold("DKMA Monster -- menu"))
        print("  g) Apply universal grants")
        for i, it in enumerate(items, 1):
            print(f"  {i}) [{it['status']:7s}] {it['title']}")
        print("  v) Verify all   c<n>) Check step n   a) Run all   q) Finish")
        try:
            choice = input("select> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if choice == "q": break
        elif choice == "g":
            grants = grant_phase(adb, pkg)
            good = sum(1 for x in grants if x["ok"])
            print(f"  grants: {good}/{len(grants)} ok")
        elif choice == "v":
            d = verify_phase(adb, pkg)
            print(f"  doze={d['in_doze_whitelist']} bucket={d['standby_bucket']}")
        elif choice.startswith("c") and choice[1:].isdigit() \
                and 1 <= int(choice[1:]) <= len(items):
            it = items[int(choice[1:]) - 1]
            v = verify_step(adb, pkg, it["def"]); it["verify"] = v
            if not v["verifiable"]:
                print("  not verifiable via API \u2014 confirm manually")
            elif v["status"] == "verified":
                it["status"] = "done"
                print("  verified \u2713 " + "; ".join(c["detail"] for c in v["checks"]))
            else:
                print("  not yet: " + "; ".join(
                    f"{c['name']} {c['detail']}" for c in v["checks"] if not c["ok"]))
        elif choice == "a":
            if not grants: grants = grant_phase(adb, pkg)
            for it in items:
                if it["status"] == "pending":
                    opened, detail = open_step_intent(adb, reg, it["def"], pkg)
                    it["status"] = "opened" if opened else "failed"; it["detail"] = detail
                    it["verify"] = verify_step(adb, pkg, it["def"])
                    if it["verify"]["verifiable"] and it["verify"]["status"] == "verified":
                        it["status"] = "done"
            print("  ran grants + opened + verified all pending steps")
        elif choice.isdigit() and 1 <= int(choice) <= len(items):
            it = items[int(choice)-1]
            opened, detail = open_step_intent(adb, reg, it["def"], pkg)
            it["status"] = "opened" if opened else "failed"; it["detail"] = detail
            print(f"  {'opened '+str(detail) if opened else 'failed to open'}")
    verify = verify_phase(adb, pkg)
    step_results = [{"id": it["id"], "title": it["title"],
                    "status": it["status"], "detail": it["detail"],
                    "verify": it.get("verify")} for it in items]
    return grants, step_results, verify

# ---------- main ------------------------------------------------------------
def main():
    global _QUIET
    ap = argparse.ArgumentParser(
        description="DKMA Monster universal ADB installer",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package", nargs="?", help="target app package, e.g. com.your.app")
    ap.add_argument("--serial", help="target a specific device serial")
    ap.add_argument("--tui", action="store_true", help="interactive checklist UI")
    ap.add_argument("--auto", action="store_true", help="grants only; skip manual pauses")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the adb commands that would run; change nothing")
    ap.add_argument("--json", action="store_true",
                    help="emit a machine-readable JSON report (implies quiet)")
    ap.add_argument("--list", action="store_true", help="list connected devices and exit")
    args = ap.parse_args()

    if args.json:
        _QUIET = True

    _p(BANNER)

    if args.list:
        devs = list_devices()
        if args.json:
            print(json.dumps({"devices": devs}, indent=2)); return
        if devs:
            print("Connected devices:")
            for d in devs: print("  -", d)
        else:
            print("No authorized devices. Enable USB debugging and accept the prompt.")
        return

    if not args.package:
        if args.json:
            print(json.dumps({"error": "no package given"})); sys.exit(EXIT_USAGE)
        fail("No package given.  Usage: python3 dkma.py com.your.app")
        sys.exit(EXIT_USAGE)
    pkg = args.package

    reg = load_registry()
    adb = Adb(args.serial, dry_run=args.dry_run)
    if args.dry_run:
        warn("DRY RUN: no changes will be made; recording intended commands.")

    facts = bring_up(adb, reg, pkg)

    if args.tui and not args.dry_run:
        grants, step_results, verify = run_tui(adb, reg, pkg, facts)
    else:
        grants, step_results, verify = run_classic(
            adb, reg, pkg, facts, auto=args.auto or args.dry_run)

    # Assemble report
    report = {
        "package": pkg,
        "device": {k: facts[k] for k in
                   ("manufacturer", "model", "brand", "android", "oem_id", "oem_label")},
        "dry_run": args.dry_run,
        "grants": grants,
        "steps": step_results,
        "verify": verify,
        "planned_commands": adb.commands if args.dry_run else [],
    }
    grant_fail = any(not g["ok"] for g in grants) and not args.dry_run
    step_fail = any(s.get("opened") is False or s.get("status") == "failed"
                    for s in step_results)
    report["success"] = not (grant_fail or step_fail)

    # Verification rollup: how many verifiable steps were actually proven.
    verifiable = [s for s in step_results
                  if s.get("verify") and s["verify"].get("verifiable")]
    verified = [s for s in verifiable if s["verify"].get("status") == "verified"]
    report["verification"] = {
        "verifiable_steps": len(verifiable),
        "verified_steps": len(verified),
        "all_verifiable_confirmed": len(verifiable) == len(verified) and bool(verifiable),
    }

    if args.dry_run:
        step("Planned commands (dry run)")
        for c in adb.commands: info(c)
        if not adb.commands: info("(no mutating commands were planned)")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        step(bold(green("Done.")))
        vr = report["verification"]
        if vr["verifiable_steps"]:
            print(f"  Verified {vr['verified_steps']}/{vr['verifiable_steps']} "
                  f"checkable steps via device APIs "
                  f"({len(step_results) - vr['verifiable_steps']} steps have no "
                  f"readable state \u2014 confirm those manually).")
        print("  The big three on any OEM: Autostart ON + Battery Unrestricted + "
              "Keep running after screen off.")
        print("  For long-lived work, also run a foreground service.")
        print("  Reference: https://dontkillmyapp.com")

    sys.exit(EXIT_OK if report["success"] else EXIT_PARTIAL)

if __name__ == "__main__":
    main()
