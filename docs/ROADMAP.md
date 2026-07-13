# Roadmap — where the Monster grows

This repo is a **starting-point masterpiece**, built to be extended. Ideas,
roughly in priority order:

## Near-term
- [ ] **More ROM component names** — the perpetual work. See CONTRIBUTING.md.
- [x] **Interactive TUI** for `dkma.py` (arrow-key checklist, per-step status).
      Shipped in v1.1: `--tui`, curses-based with a numbered-menu fallback.
- [x] **`--dry-run`** that prints every command without executing. Shipped v1.1.
- [x] **JSON/exit-code output mode** for CI and QA farms. Shipped v1.1:
      `--json` report + exit codes `0/1/2/3`.
- [x] **Per-step verification** (re-read state after each toggle where possible).
      Shipped v1.6: `verify_step()` proves each step via Doze/appops/standby where
      an API exists; unverifiable steps are honestly flagged. Wired into the CLI,
      TUI, numbered menu, GUI (`/api/verify-step`) and all JSON reports.

## Mid-term
- [x] **Desktop GUI** (Tauri/Electron): plug in phone, pick app, click Fix.
      Shipped v1.3 as a dependency-free variant: `gui/server.py` (stdlib web
      server wrapping the `dkma.py` engine) + `gui/index.html`. Preview without a
      phone via `gui/preview.html`.
- [x] **In-app compose UI kit** — ready-made wizard screens for `DkmaMonster.kt`.
      Shipped v1.2: `android/DkmaWizard.kt` (full screen + bottom sheet) with an
      interactive HTML preview at `android/preview/DkmaWizard-preview.html`.
- [x] **Autostart state read** via the MIUI-autostart technique, wired into the
      app so it only nags when actually disabled. Shipped v1.7:
      `android/DkmaAutostart.kt` (reflection over the hidden AppOps op, no deps);
      `DkmaMonster.autostartState()`; wizard shows a Verified chip.
- [x] **KMP bindings** around the same registry. Shipped v1.8: `kmp/` module
      (commonMain `DkmaCore` + generated `DkmaRegistryData`, `expect/actual`
      `PlatformOps` for android/jvm/ios/js, shared tests). Flutter / React-Native
      wrappers can bind to this next.
- [x] **Registry as a package** consumed by all layers (generate Kotlin from JSON
      so the app and ADB never drift). Shipped v1.5: `tools/gen_kotlin_registry.py`
      generates `android/DkmaRegistry.kt`; `tools/build_all.py --check` + CI guard
      against drift; the web generator now reads hints from the JSON too.

## Long-term
- [x] **Web dashboard** that serves the registry + per-device instructions
      (like dontkillmyapp.com, but self-hostable). Shipped v1.4:
      `web/build.py` generates a searchable static site into `web/site/` from
      `oem_registry.json`. (Screenshots still TODO.)
- [ ] **Telemetry-free health check**: an in-app self-test that detects "I was
      killed" events and prompts re-running the guided setup.
- [ ] **Magisk WebUI** to manage the apps.list from the phone.
- [ ] **Root op expansion**: map more vendor secure-settings keys / DB writes.

## Non-goals
- Shipping malware-y persistence or hiding from the user.
- Pretending stock no-root can do what only root can. Honesty is a feature.
