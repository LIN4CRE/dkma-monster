# DKMA Monster — tools (single-source codegen)

`data/oem_registry.json` is the **one source of truth** for every layer. These
tools generate the derived artifacts so nothing is ever hand-mirrored again.

| Tool | What it does |
|---|---|
| `gen_kotlin_registry.py` | Generates `android/DkmaRegistry.kt` from the JSON. `--check` fails if it's stale. |
| `build_all.py` | Validates the registry, then regenerates the Kotlin registry **and** the web dashboard. `--check` for CI. |

## Usage

```bash
# Regenerate everything after editing the registry
python3 tools/build_all.py

# CI / pre-commit: fail if anything is out of sync
python3 tools/build_all.py --check
```

## What consumes the registry now

```
                    data/oem_registry.json   ← edit ONLY this
                              │
      ┌───────────┬──────────┼───────────┬─────────────────┐
      ▼           ▼          ▼           ▼                 ▼
  adb/dkma.py  gui/server  web/build.py  tools/gen_…  root/dkma-root.sh
  (reads JSON) (reads JSON) (reads JSON) → DkmaRegistry.kt  (case match)
                                              │
                                       android/DkmaMonster.kt (consumes it)
```

- The **CLI, GUI, and web generator read the JSON at runtime/build time**, so
  they can't drift.
- The **in-app Kotlin library** can't read the file at build time, so
  `gen_kotlin_registry.py` compiles it into `DkmaRegistry.kt`. The drift check
  guarantees that generated file always matches the JSON.

## Adding / editing an OEM
1. Edit `data/oem_registry.json` (see `../docs/CONTRIBUTING.md`).
2. Run `python3 tools/build_all.py`.
3. Commit the JSON **and** the regenerated `android/DkmaRegistry.kt` + `web/site/`.

CI (`.github/workflows/ci.yml`) runs `build_all.py --check` and fails the build
if the generated Kotlin wasn't regenerated.

## Note
Never hand-edit `android/DkmaRegistry.kt` — it has a "GENERATED — DO NOT EDIT"
header and will be overwritten.
