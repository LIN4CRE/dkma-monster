# Changelog

## v1.9.0 — Linacre theme + GitHub prep
- Visual overhaul across the web dashboard, desktop GUI and both HTML previews to
  the **Linacre** brand language: Ink Black backgrounds, Amber Core/Glow accents,
  brand gradients + glow shadows, hexagon logo/step badges, glassmorphism sticky
  header with a breathing logo, amber pulse-line dividers, Space Grotesk type and
  terminal touches ("/" to search, `$ dkma` prompt).
- Added a polished GitHub `README.md` (badges, architecture diagram, honest-limits
  section, per-vector quick start), `.gitignore`, and "Built by David Linacre ·
  linacre.site" byline in footers + LICENSE.
- Full bug sweep: all artifacts regenerated, single-source drift checks pass, all
  Python compiles, all Kotlin brace-balanced, shell scripts lint, and CLI + GUI
  verified end-to-end against a mock adb.

## v1.8.0 — Kotlin Multiplatform bindings
- **`kmp/`**: a Kotlin Multiplatform module sharing the OEM registry + detection
  logic across Android / iOS / JVM / JS.
  - `commonMain/DkmaCore.kt` — pure, platform-agnostic detection & step resolution.
  - `commonMain/DkmaRegistryData.kt` — **generated** from the JSON registry.
  - `expect object PlatformOps` with `actual`s for android/jvm/ios/js
    (Android reads `Build.*` and opens Settings; others are sensible no-ops).
  - `commonTest/DkmaCoreTest.kt` — shared tests for detection, components, extras.
  - `build.gradle.kts` + `kmp/README.md`.
- **`tools/gen_kmp_registry.py`**: generates the KMP data; wired into
  `tools/build_all.py` and its `--check` drift guard; CI updated.

## v1.7.0 — Authoritative autostart read
- **`android/DkmaAutostart.kt`**: reads the real MIUI/HyperOS Autostart state via
  reflection over the hidden AppOps op (the MIUI-autostart technique), with
  **zero dependencies**. Returns `ENABLED` / `DISABLED` / `UNKNOWN` / `UNSUPPORTED`.
- **`DkmaMonster`**: new `autostartState(ctx)`; `needsAttention()` now also returns
  true when autostart is provably disabled (so you only nag when it's really off).
- **`DkmaWizard`**: shows a **Verified** chip and auto-ticks the Autostart step
  when it can prove the permission is ON; re-checks on resume.
- Wizard HTML preview gains a "Simulate: read Autostart via AppOps" control.
- Docs updated (android/README) with the new API and honest capability notes.

## v1.6.0 — Per-step live verification
- **`verify_step()`** in the engine: after each step, re-reads device state to
  prove whether it took effect — Doze whitelist, background appops
  (`RUN_ANY_IN_BACKGROUND`, `AUTO_START`), and standby bucket — via a
  `VERIFY_MAP` keyed by step id. Returns `verified` / `not_yet` / `unverifiable`.
- Honest by design: steps with no readable API (MIUI optimizations, protected
  apps, battery profile, sleeping apps) are flagged `unverifiable` instead of
  being claimed as done.
- Wired everywhere:
  - **CLI classic** — per-step verify line + a "verified N/M checkable steps" summary.
  - **TUI** — new `c` (check step) key; `a` (run all) opens *and* verifies; steps
    auto-flip to done when proven.
  - **Numbered menu** — `c<n>` to check a step; `a` verifies all.
  - **GUI** — new `/api/verify-step`; `open-step` and `fix` now return per-step
    `verify`; the UI shows verified/not-confirmed/confirm-manually pills.
  - **JSON report** — each step carries `verify`; a `verification` rollup added.
- Added the missing `re` import used by appop parsing.

## v1.5.0 — True single source of truth (codegen + drift guard)
- **`tools/gen_kotlin_registry.py`**: generates `android/DkmaRegistry.kt` from
  `data/oem_registry.json`, so the in-app library is no longer hand-mirrored.
  `--check` fails if the generated file is stale.
- **`android/DkmaMonster.kt`** refactored to consume the generated `DkmaRegistry`
  (removed ~170 lines of hand-maintained OEM data that had already drifted, e.g.
  OnePlus steps). Detection/intents exposed as `internal` for the generated file.
- **`data/oem_registry.json`**: step `hint` copy moved into the JSON so the app
  wizard and web dashboard share the same wording.
- **`web/build.py`** now reads hints from the JSON (single source) instead of its
  own duplicate map.
- **`tools/build_all.py`**: one command to validate the registry and regenerate
  the Kotlin registry + web site; `--check` mode for CI.
- **`.github/workflows/ci.yml`**: validates the registry, checks Kotlin drift,
  compiles all Python entrypoints, and fails if generated files weren't rebuilt.
- **`tools/README.md`** + updated `docs/CONTRIBUTING.md` (adding an OEM is now a
  JSON edit + `build_all.py`, no hand-mirroring).

## v1.4.0 — Self-hostable web dashboard
- **`web/build.py`**: a stdlib-only static-site generator that turns
  `data/oem_registry.json` into a searchable keep-alive guide — index page with
  brand search + the "big three", and one step-by-step page per OEM family (15).
- Registry stays the single source of truth: technical data comes from the JSON,
  friendly copy from a `STEP_GUIDE` map; each page includes a Developer
  disclosure of the exact settings Activities the tools open.
- Fully static (inline CSS/JS, no external assets) — host anywhere or view
  offline. Output in `web/site/`.
- **`web/README.md`**: build/serve instructions and content model.

## v1.3.0 — Desktop GUI
- **`gui/server.py`**: a dependency-free (Python stdlib) local web server that
  imports `adb/dkma.py` as a module and exposes it over JSON — so GUI and CLI
  share one engine and can never drift.
- **`gui/index.html`**: a self-contained dark-theme UI — device picker (with
  auto-detected OEM), filterable app list, tailored keep-alive steps, one-click
  **Fix everything** / **Dry run**, live verification, and an activity log.
- **`gui/preview.html`**: a mock-data build of the UI (Xiaomi + Samsung demo
  devices) that runs with no server or phone, for instant viewing.
- **`gui/README.md`**: run instructions, architecture, and endpoint reference.
- Endpoints: `/api/devices`, `/api/packages`, `/api/inspect`, `/api/open-step`,
  `/api/fix` (with dry-run). Tested end-to-end against a mock adb.

## v1.2.0 — In-app Compose wizard UI kit
- **`android/DkmaWizard.kt`**: a drop-in Jetpack Compose wizard rendered on top
  of `DkmaMonster` — OEM-aware checklist, animated progress, per-step cards with
  hints, "Open settings"/"Done" actions, plus `DkmaWizardBottomSheet`.
- **Auto-verification**: the battery-optimization exemption is re-checked on every
  resume via `LifecycleResumeEffect`; its card flips to green automatically.
- **`Step.hint`** field added to `DkmaMonster.kt` (backward-compatible) and
  populated for the major OEMs, so the wizard shows real per-step guidance.
- **`android/preview/DkmaWizard-preview.html`**: an interactive, browser-viewable
  mockup driven by the same registry data, with a dropdown to preview all 16
  device profiles — no Android build required.
- **`android/README.md`**: Gradle deps, usage, and honest capability notes.

## v1.1.0 — ADB installer power-up
- **Interactive TUI** (`--tui`): keyboard-driven checklist (curses) with live
  per-step status, plus an automatic numbered-menu fallback when `curses` is
  unavailable (bare Windows shells, minimal Pythons).
- **`--dry-run`**: prints every mutating adb command that *would* run and changes
  nothing. Read-only detection commands still run so OEM profiling stays accurate.
- **`--json`**: machine-readable report (device facts, per-grant results, per-step
  open results, verification, and — in dry-run — the planned command list). Ideal
  for CI and QA device farms.
- **Exit codes**: `0` success · `1` usage/device error · `2` adb missing ·
  `3` completed with partial failures.
- Internal refactor: shared `bring_up` / `grant_phase` / `verify_phase` /
  `open_step_intent` core used by classic, TUI, and menu paths.

## v1.0.0 — initial universal release
- OEM registry (`data/oem_registry.json`) covering 15 vendor families.
- Cross-platform ADB installer (`adb/dkma.py`) with OEM auto-detection.
- Fully-automatic root installer (`root/dkma-root.sh`).
- Persistent Magisk module (`magisk/`) re-applying settings on every boot.
- Universal in-app Kotlin library (`android/DkmaMonster.kt`).
- Docs: HOW-IT-WORKS, CONTRIBUTING, ROADMAP; MIT license.
