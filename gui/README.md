# DKMA Monster — Desktop GUI

A friendly point-and-click front end for the ADB engine. **Plug in your phone →
pick the app → click Fix.** No install, no dependencies — it's a tiny Python
stdlib web server that drives the exact same `dkma.py` engine as the CLI.

> 👀 **See it without a phone:** open `gui/preview.html` — a self-contained demo
> with mock devices (Xiaomi + Samsung) and fake data, so the whole UI is
> clickable in your browser or the in-app viewer. The *real* app is `index.html`
> served by `server.py`.

## Run it

```bash
# prerequisites: adb on PATH + USB debugging enabled on the phone
python3 gui/server.py
# → opens http://127.0.0.1:8765 in your browser
```

Options:
```
--port 9000     # change the port (default 8765)
--host 0.0.0.0  # bind address (default 127.0.0.1, local-only)
--no-open       # don't auto-launch the browser
```

## What it does

1. **Device** — lists every authorized device with make/model, Android version
   and the auto-detected OEM profile. Multi-device friendly; click to select.
2. **App** — lists user-installed packages (filterable) for the chosen device.
3. **Keep-alive steps** — shows the exact steps tailored to that OEM. Open any
   single vendor screen, or hit:
   - **⚡ Fix everything** — applies all ADB grants (Doze whitelist, standby
     bucket, background appops) and opens each vendor screen in order.
   - **Dry run** — shows every command it *would* run, changing nothing.
4. **Verify** — live readout of the Doze-whitelist and standby-bucket state.
5. **Activity log** — a timestamped transcript of every action.

## Architecture

```
 browser (index.html)  ──HTTP/JSON──►  server.py  ──imports──►  ../adb/dkma.py
   plain HTML/CSS/JS                   stdlib only              the one engine
```

`server.py` imports `dkma.py` as a module and calls its functions directly
(`api_devices`, `api_packages`, `api_inspect`, `api_open_step`, `api_fix`), so
the GUI and CLI can never drift. All endpoints return JSON; errors (e.g. adb
missing) come back as `{"error": "..."}` with a 500.

## Honest limits
Same as everywhere in this repo: grants are automatic, but Autostart /
OEM-optimization / protected-app toggles have no public API, so those steps open
the vendor screen for you to confirm. For full automation use the root installer
or Magisk module.

## Endpoints (for scripting / a future native shell)
| Method | Path | Body / query | Returns |
|---|---|---|---|
| GET | `/api/devices` | — | `{devices:[…]}` |
| GET | `/api/packages` | `?serial=` | `{packages:[…]}` |
| GET | `/api/inspect` | `?serial=&package=` | `{oem_label, steps, verify}` |
| POST | `/api/open-step` | `{serial,package,step_id}` | `{opened, detail, verify}` |
| POST | `/api/verify-step` | `{serial,package,step_id}` | `{verify}` (re-reads state, no side effects) |
| POST | `/api/fix` | `{serial,package,dry_run}` | full report + `verification` + `success` |

### Per-step verification
After opening a step, the backend re-reads device state to prove whether it
actually took effect: Doze whitelist, background appops, and standby bucket. Each
step reports `verified`, `not_yet`, or `unverifiable` (no readable API on stock —
confirm manually). The UI shows a coloured pill per step and a verified/verifiable
rollup on **Fix**.
