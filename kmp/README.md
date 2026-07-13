# DKMA Monster — Kotlin Multiplatform module

The shared OEM registry + detection logic as a **Kotlin Multiplatform** library,
so Android, iOS, JVM (desktop/server) and JS (web/Node) apps can all reuse the
same "Don't Kill My App!" knowledge from one codebase.

## What's here

```
kmp/
├── build.gradle.kts
└── src/
    ├── commonMain/…/DkmaRegistryData.kt   # GENERATED from oem_registry.json
    ├── commonMain/…/DkmaCore.kt           # detection + step resolution (pure)
    ├── commonTest/…/DkmaCoreTest.kt       # shared tests
    ├── androidMain/…/PlatformOps.android.kt  # reads Build.*, opens Settings
    ├── jvmMain/…/PlatformOps.jvm.kt          # test/desktop (opening = no-op)
    ├── iosMain/…/PlatformOps.ios.kt          # generic profile, no-op open
    └── jsMain/…/PlatformOps.js.kt            # generic profile, no-op open
```

- **`DkmaRegistryData.kt`** is generated — never hand-edit it. Regenerate with
  `python3 tools/gen_kmp_registry.py` (or `python3 tools/build_all.py`).
- **`DkmaCore`** is platform-agnostic: `detect()`, `stepsFor()`, `componentsFor()`,
  `extrasFor()`, `bigThree`. No Android types.
- **`PlatformOps`** is an `expect object` with per-target `actual`s for the few
  device-specific bits (reading the device signature, opening a settings screen,
  battery-optimization check).

## Using it from shared code

```kotlin
val oem   = DkmaCore.detect(PlatformOps.deviceInfo())
val steps = DkmaCore.stepsFor(oem)          // List<RegStep>

// Show `steps` in your shared UI, then on tap:
PlatformOps.openStep(steps[i], "com.your.app")
```

On Android, initialise the context once:
```kotlin
class App : Application() {
    override fun onCreate() { super.onCreate(); DkmaAndroid.init(this) }
}
```

## Building & testing

Standard KMP Gradle (needs the Kotlin & Android Gradle plugins from the module's
`build.gradle.kts`):

```bash
./gradlew :kmp:allTests        # run commonTest across configured targets
./gradlew :kmp:assemble        # build all target artifacts
```

## Relationship to the other layers
This module reads the **same** `data/oem_registry.json` as the CLI, GUI, web
dashboard and the standalone Android library. `tools/build_all.py` regenerates
both the Android `DkmaRegistry.kt` and this module's `DkmaRegistryData.kt`, and
CI drift-checks both — so nothing can fall out of sync.

> The standalone `android/DkmaMonster.kt` (+ `DkmaAutostart`, `DkmaWizard`)
> remains the zero-dependency, Android-only option. Use **this KMP module** when
> you want to share the logic across platforms.
