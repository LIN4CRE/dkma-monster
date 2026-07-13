package dkma.monster

/**
 * DKMA Monster — Kotlin Multiplatform core (commonMain).
 *
 * Platform-agnostic OEM detection and step resolution shared across Android,
 * iOS, JVM and JS. It carries no platform types; anything device-specific
 * (reading Build.MANUFACTURER, opening a settings screen) is provided by the
 * platform via [DeviceInfo] / the `expect` [PlatformOps].
 *
 * Typical use from shared code:
 *
 *     val oem = DkmaCore.detect(currentDeviceInfo())
 *     val steps = DkmaCore.stepsFor(oem)
 *     // hand `steps` to your UI; call platform code to open each one.
 */

/** Minimal, platform-neutral device signature used for OEM matching. */
public data class DeviceInfo(
    val manufacturer: String,
    val brand: String,
    /** Map of system-property key -> value, for prop-based matching. */
    val props: Map<String, String> = emptyMap(),
)

public object DkmaCore {

    public val registryVersion: String get() = DkmaRegistryData.REGISTRY_VERSION

    /** All known OEM profiles (generated from the JSON registry). */
    public val oems: List<RegOem> get() = DkmaRegistryData.OEMS

    /**
     * Detect the OEM profile for a device signature, or the generic profile if
     * none matches. Matching mirrors every other DKMA layer: manufacturer or
     * brand substring, or presence of any signature system property.
     */
    public fun detect(info: DeviceInfo): RegOem {
        val manuf = info.manufacturer.lowercase()
        val brand = info.brand.lowercase()
        for (oem in DkmaRegistryData.OEMS) {
            if (oem.manufacturer.any { manuf.contains(it) }) return oem
            if (oem.brand.any { brand.contains(it) }) return oem
            if (oem.props.any { (info.props[it] ?: "").isNotBlank() }) return oem
        }
        return DkmaRegistryData.GENERIC
    }

    /** The ordered steps a given OEM needs. */
    public fun stepsFor(oem: RegOem): List<RegStep> = oem.steps

    /** Convenience: detect + steps in one call. */
    public fun stepsFor(info: DeviceInfo): List<RegStep> = stepsFor(detect(info))

    /**
     * The ordered candidate component strings ("pkg/activity") for a step,
     * for platforms that open settings by component. Empty if the step is
     * intent/`use`-based only.
     */
    public fun componentsFor(step: RegStep, pkg: String): List<Pair<String, String>> =
        step.components.map {
            val i = it.indexOf('/')
            it.substring(0, i) to it.substring(i + 1)
        }.also { /* pkg reserved for future %PKG% substitution in components */ }

    /** Resolve a step's extras with %PKG% substituted. */
    public fun extrasFor(step: RegStep, pkg: String): Map<String, String> =
        step.extras.mapValues { (_, v) -> v.replace("%PKG%", pkg) }

    /** The "big three" summary shown by every DKMA front end. */
    public val bigThree: List<String> = listOf(
        "Autostart / auto-launch \u2192 ON",
        "Battery \u2192 Unrestricted / No restrictions",
        "Keep running after screen off",
    )
}

/**
 * Platform hooks. Each target provides an `actual` implementation:
 *   - androidMain: reads Build.* and opens Settings via Intents.
 *   - iosMain/jvmMain/jsMain: return best-effort info; opening is a no-op or
 *     deep-links to the OS settings where possible.
 */
public expect object PlatformOps {
    /** Current device signature for OEM matching. */
    public fun deviceInfo(): DeviceInfo

    /** Open a step's settings screen for [pkg]. Returns true if something opened. */
    public fun openStep(step: RegStep, pkg: String): Boolean

    /** True if the app is exempt from battery optimization (where knowable). */
    public fun isBatteryOptimizationIgnored(pkg: String): Boolean
}
