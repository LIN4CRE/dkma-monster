# How DKMA Monster works

## The three layers of Android background killing

1. **Stock Android (Doze, App Standby, background limits).** Documented, has
   APIs. DKMA handles these fully & automatically everywhere:
   - `dumpsys deviceidle whitelist +pkg` → Doze exemption
   - `am set-standby-bucket pkg active` → keeps the app in the active bucket
   - `cmd appops set pkg RUN_IN_BACKGROUND/RUN_ANY_IN_BACKGROUND/START_FOREGROUND allow`

2. **OEM battery managers (MIUI, EMUI, ColorOS, One UI, Funtouch…).**
   Undocumented, mostly **no API**. Some expose an *appop* (e.g. `AUTO_START`)
   that root can flip; the rest are UI-only. DKMA:
   - tries the vendor appop (root/ADB, best-effort), and
   - deep-links the user to the exact vendor Activity for the manual toggle.

3. **App-level design.** No setting beats a correct **foreground service** with
   the right FGS type for long-lived work. DKMA reminds you; it can't write your
   service.

## Why deep-linking needs a registry

Each OEM buries the toggle in a differently-named Activity, and those names
change across ROM versions. `data/oem_registry.json` stores an **ordered list of
candidate components** per step; the tools try each until one launches, then fall
back to the generic App-info page. That's why adding a ROM is just a JSON edit.

## What each tool can and cannot do

| | ADB (no root) | Root / Magisk |
|---|---|---|
| Doze whitelist | ✅ | ✅ |
| Standby bucket | ✅ | ✅ |
| Background appops | ✅ | ✅ |
| Vendor autostart appop | ⚠️ sometimes | ✅ where it exists |
| MIUI optimizations / Protected apps / battery profile | ❌ (guided tap) | ⚠️ partial |
| Survives reboot automatically | ❌ | ✅ (Magisk) |

## Verification

### Per-step verification (CLI, TUI, and GUI)
After each step, the tools re-read device state to **prove** whether the change
took effect, mapping each step id to what's actually checkable:

| Step | Proven with | API? |
|---|---|---|
| battery optimization / stamina / recent-lock | `dumpsys deviceidle whitelist` | ✅ |
| app_details (background/battery) | appop `RUN_ANY_IN_BACKGROUND` = allow **and** standby bucket ∈ {active, working_set} | ✅ |
| autostart | appop `AUTO_START` = allow (where the ROM exposes it) | ⚠️ ROM-dependent |
| MIUI optimizations / protected apps / battery profile / sleeping apps | *no readable state* | ❌ → `unverifiable` |

Each step returns one of `verified`, `not_yet`, or `unverifiable`. The last is
reported honestly ("confirm the toggle manually") rather than pretending success.
The final report includes a `verification` rollup (`verified_steps` /
`verifiable_steps`).

### Final read-back
Both installers also finish by reading:
- `dumpsys deviceidle whitelist` (should contain your package)
- `am get-standby-bucket pkg` (should be `active`/`working_set`)

The Magisk module logs every boot pass to `/data/adb/dkma/dkma.log`.
