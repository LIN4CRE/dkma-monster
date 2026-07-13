#!/usr/bin/env python3
# =============================================================================
#  DKMA MONSTER  --  Desktop GUI backend (stdlib only)
#  A tiny local web server that wraps the dkma.py engine so you can keep apps
#  alive from a friendly browser UI: plug in phone -> pick app -> click Fix.
#
#  Usage:   python3 gui/server.py            # opens http://127.0.0.1:8765
#           python3 gui/server.py --port 9000 --no-open
#
#  No third-party dependencies. Requires adb on PATH (same as the CLI).
# =============================================================================
import argparse
import importlib.util
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_PATH = os.path.join(HERE, "..", "adb", "dkma.py")
INDEX_PATH = os.path.join(HERE, "index.html")

# ---- import the CLI engine as a module (single source of truth) -------------
def load_engine():
    spec = importlib.util.spec_from_file_location("dkma_engine", ENGINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    mod._QUIET = True            # silence the engine's console prints
    spec.loader.exec_module(mod)
    mod._QUIET = True
    return mod

ENGINE = load_engine()
REG = ENGINE.load_registry()

# ---- adb-backed operations --------------------------------------------------
def _adb(serial=None, dry_run=False):
    return ENGINE.Adb(serial or None, dry_run=dry_run)

def api_devices():
    """Rich device list: serial + manufacturer/model + detected OEM."""
    out = []
    for serial in ENGINE.list_devices():
        adb = _adb(serial)
        manuf = adb.getprop("ro.product.manufacturer")
        model = adb.getprop("ro.product.model")
        brand = adb.getprop("ro.product.brand")
        android = adb.getprop("ro.build.version.release")
        props = {p: adb.getprop(p) for o in REG["oems"]
                 for p in o["match"].get("props", [])}
        oem = ENGINE.detect_oem(REG, manuf, brand, props)
        out.append({
            "serial": serial, "manufacturer": manuf, "model": model,
            "brand": brand, "android": android,
            "oem_id": oem["id"] if oem else "generic",
            "oem_label": oem["label"] if oem else "Generic / Stock Android",
        })
    return {"devices": out}

def api_packages(serial):
    """Third-party (user-installed) packages, sorted."""
    adb = _adb(serial)
    _, out, _ = adb.shell(["pm", "list", "packages", "-3"])
    pkgs = sorted(l.split("package:")[-1] for l in out.splitlines()
                  if l.startswith("package:"))
    return {"packages": pkgs}

def api_inspect(serial, package):
    """Non-destructive: detect OEM + planned steps + current battery state."""
    adb = _adb(serial, dry_run=True)  # dry-run: reads only, records nothing dangerous
    manuf = adb.getprop("ro.product.manufacturer")
    brand = adb.getprop("ro.product.brand")
    props = {p: adb.getprop(p) for o in REG["oems"]
             for p in o["match"].get("props", [])}
    oem = ENGINE.detect_oem(REG, manuf, brand, props)
    steps = ENGINE.steps_for(REG, oem)
    verify = ENGINE.verify_phase(adb, package)
    return {
        "oem_id": oem["id"] if oem else "generic",
        "oem_label": oem["label"] if oem else "Generic / Stock Android",
        "steps": [{"id": s.get("id"), "title": s.get("title", s.get("id"))}
                  for s in steps],
        "verify": verify,
    }

def api_open_step(serial, package, step_id):
    """Open one vendor settings screen on the device."""
    adb = _adb(serial)
    oem = None
    manuf = adb.getprop("ro.product.manufacturer")
    brand = adb.getprop("ro.product.brand")
    props = {p: adb.getprop(p) for o in REG["oems"]
             for p in o["match"].get("props", [])}
    oem = ENGINE.detect_oem(REG, manuf, brand, props)
    for s in ENGINE.steps_for(REG, oem):
        if s.get("id") == step_id:
            opened, detail = ENGINE.open_step_intent(adb, REG, s, package)
            return {"opened": opened, "detail": detail, "step_id": step_id,
                    "verify": ENGINE.verify_step(adb, package, s)}
    return {"opened": False, "detail": None, "step_id": step_id,
            "error": "step not found"}

def api_verify_step(serial, package, step_id):
    """Re-read device state to prove a single step took effect (no side effects)."""
    adb = _adb(serial)
    manuf = adb.getprop("ro.product.manufacturer")
    brand = adb.getprop("ro.product.brand")
    props = {p: adb.getprop(p) for o in REG["oems"]
             for p in o["match"].get("props", [])}
    oem = ENGINE.detect_oem(REG, manuf, brand, props)
    for s in ENGINE.steps_for(REG, oem):
        if s.get("id") == step_id:
            return {"step_id": step_id,
                    "verify": ENGINE.verify_step(adb, package, s)}
    return {"step_id": step_id, "error": "step not found"}

def api_fix(serial, package, dry_run=False):
    """Full run: grants + open each step. Returns a report like `dkma.py --json`."""
    adb = _adb(serial, dry_run=dry_run)
    grants = ENGINE.grant_phase(adb, package)
    manuf = adb.getprop("ro.product.manufacturer")
    brand = adb.getprop("ro.product.brand")
    props = {p: adb.getprop(p) for o in REG["oems"]
             for p in o["match"].get("props", [])}
    oem = ENGINE.detect_oem(REG, manuf, brand, props)
    steps_out = []
    for s in ENGINE.steps_for(REG, oem):
        opened, detail = ENGINE.open_step_intent(adb, REG, s, package)
        step_verify = None if dry_run else ENGINE.verify_step(adb, package, s)
        steps_out.append({"id": s.get("id"),
                          "title": s.get("title", s.get("id")),
                          "opened": opened, "detail": detail,
                          "verify": step_verify})
    verify = ENGINE.verify_phase(adb, package)
    grant_ok = all(g["ok"] for g in grants) or dry_run
    step_ok = all(s["opened"] for s in steps_out)
    verifiable = [s for s in steps_out if s.get("verify")
                  and s["verify"].get("verifiable")]
    verified = [s for s in verifiable if s["verify"].get("status") == "verified"]
    return {
        "package": package,
        "dry_run": dry_run,
        "grants": grants,
        "steps": steps_out,
        "verify": verify,
        "verification": {"verifiable_steps": len(verifiable),
                         "verified_steps": len(verified)},
        "planned_commands": adb.commands if dry_run else [],
        "success": bool(grant_ok and step_ok),
    }

# ---- HTTP layer -------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # keep the console quiet
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj), "application/json")

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            return {}

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                with open(INDEX_PATH, "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            if u.path == "/api/devices":
                return self._json(api_devices())
            if u.path == "/api/packages":
                return self._json(api_packages(q.get("serial", [""])[0]))
            if u.path == "/api/inspect":
                return self._json(api_inspect(q.get("serial", [""])[0],
                                              q.get("package", [""])[0]))
            return self._json({"error": "not found"}, 404)
        except SystemExit:
            return self._json({"error": "adb not found on PATH"}, 500)
        except Exception as e:
            return self._json({"error": str(e)}, 500)

    def do_POST(self):
        u = urlparse(self.path)
        body = self._read_body()
        try:
            if u.path == "/api/open-step":
                return self._json(api_open_step(body.get("serial"),
                                                body.get("package"),
                                                body.get("step_id")))
            if u.path == "/api/verify-step":
                return self._json(api_verify_step(body.get("serial"),
                                                  body.get("package"),
                                                  body.get("step_id")))
            if u.path == "/api/fix":
                return self._json(api_fix(body.get("serial"),
                                          body.get("package"),
                                          bool(body.get("dry_run"))))
            return self._json({"error": "not found"}, 404)
        except SystemExit:
            return self._json({"error": "adb not found on PATH"}, 500)
        except Exception as e:
            return self._json({"error": str(e)}, 500)

def main():
    ap = argparse.ArgumentParser(description="DKMA Monster desktop GUI")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-open", action="store_true",
                    help="don't auto-open the browser")
    args = ap.parse_args()

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    print(f"DKMA Monster GUI running at {url}")
    print("Plug in your phone (USB debugging on) and refresh the page. Ctrl+C to quit.")
    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nBye.")
        srv.shutdown()

if __name__ == "__main__":
    main()
