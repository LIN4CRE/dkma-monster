# DKMA Monster — Android in-app kit

Two drop-in files, zero-to-minimal dependencies:

| File | What it is | Dependencies |
|---|---|---|
| `DkmaMonster.kt` | The engine: OEM detection + deep-links to every vendor keep-alive screen for ~15 families | none |
| `DkmaRegistry.kt` | **Generated** OEM data (from `data/oem_registry.json`). Do not edit — run `python3 tools/build_all.py` | none |
| `DkmaWizard.kt` | Optional Jetpack Compose **wizard UI kit** that renders a friendly checklist on top of the engine | Compose Material3 + lifecycle-runtime-compose |
| `preview/DkmaWizard-preview.html` | An interactive, browser-viewable mockup of the wizard (switch between all 16 device profiles) | — |

> **Preview it now:** open `preview/DkmaWizard-preview.html`. Use the *Preview
> device* dropdown to see the exact steps each OEM gets, and tap the buttons to
> watch the live state (progress bar, battery card, done badges).

---

## 1. Engine only (no Compose)

```kotlin
if (DkmaMonster.needsAttention(context)) {
    DkmaMonster.runGuidedSetup(activity)   // opens each required screen in order
}
```
Or build your own UI from `DkmaMonster.stepsFor(context)` and
`DkmaMonster.openStep(context, step)`.

## 2. The Compose wizard (recommended)

Full screen:
```kotlin
setContent {
    MaterialTheme {
        DkmaWizardScreen(onFinish = { finish() })
    }
}
```

As a bottom sheet from anywhere:
```kotlin
var show by remember { mutableStateOf(false) }
if (show) DkmaWizardBottomSheet(onDismiss = { show = false })
```

Only prompt when it actually matters:
```kotlin
LaunchedEffect(Unit) {
    if (DkmaMonster.needsAttention(context)) show = true
}
```

### Gradle
```kotlin
dependencies {
    implementation platform("androidx.compose:compose-bom:2024.06.00")
    implementation "androidx.compose.material3:material3"
    implementation "androidx.compose.material:material-icons-extended"
    implementation "androidx.activity:activity-compose:1.9.0"
    implementation "androidx.lifecycle:lifecycle-runtime-compose:2.8.0"
}
```
(Any recent Compose BOM works; these are just known-good versions.)

### Manifest
Merge `AndroidManifest-snippet.xml` for the standard permissions
(`REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, `RECEIVE_BOOT_COMPLETED`, foreground
service types, `POST_NOTIFICATIONS`, `WAKE_LOCK`).

---

## What the wizard does (and honestly can't)

- ✅ **Detects the OEM** and shows only the steps that device needs.
- ✅ **Auto-verifies** the battery-optimization exemption and re-checks it every
  time the user returns to the app (`LifecycleResumeEffect`). The battery card
  turns green automatically.
- ✅ **Authoritative Autostart read** on MIUI/HyperOS via `DkmaAutostart` (pure
  reflection over the hidden AppOps op — the technique the MIUI-autostart library
  uses, with **no dependency**). When it can prove Autostart is ON, the wizard
  shows a **Verified** chip and auto-ticks that step; `needsAttention()` also
  factors this in so you only nag when it's genuinely off.
- ✅ **Deep-links** straight to each vendor screen (Autostart, battery profile,
  protected apps, sleeping apps…), with graceful fallback to App-info.
- ⚠️ **Cannot read** OEM-optimization / protected-app / battery-profile toggles —
  no public API — so the user confirms those with the **Done** button. The wizard
  is upfront about this in its footer.

### Authoritative autostart API
```kotlin
when (DkmaAutostart.getState(context)) {
    DkmaAutostart.State.ENABLED     -> // proven ON  → don't nag
    DkmaAutostart.State.DISABLED    -> // proven OFF → send to Autostart screen
    DkmaAutostart.State.UNKNOWN     -> // couldn't read → fall back to guiding
    DkmaAutostart.State.UNSUPPORTED -> // ROM has no readable autostart op
}
```

## Extending
Add or fix a step in `data/oem_registry.json` (with an optional `hint`), then run
`python3 tools/build_all.py` to regenerate `DkmaRegistry.kt` — it shows up in the
wizard automatically. See `../docs/CONTRIBUTING.md`.

## Files
- `DkmaMonster.kt` — engine (detection, deep-links, `needsAttention`, `autostartState`)
- `DkmaAutostart.kt` — authoritative autostart reader (reflection, no deps)
- `DkmaRegistry.kt` — generated OEM data (do not edit)
- `DkmaWizard.kt` — Compose wizard UI kit
