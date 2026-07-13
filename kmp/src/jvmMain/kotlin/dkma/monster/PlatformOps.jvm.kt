package dkma.monster

/**
 * JVM `actual` for [PlatformOps]. Useful for tests, tooling and desktop apps.
 * Reads OEM info from system properties you can inject via -D flags for testing
 * (dkma.manufacturer / dkma.brand). Opening a settings screen is a no-op on a
 * plain JVM (there is no phone), returning false so callers can guide the user.
 */
public actual object PlatformOps {

    public actual fun deviceInfo(): DeviceInfo = DeviceInfo(
        manufacturer = System.getProperty("dkma.manufacturer", ""),
        brand = System.getProperty("dkma.brand", ""),
        props = emptyMap(),
    )

    public actual fun openStep(step: RegStep, pkg: String): Boolean = false

    public actual fun isBatteryOptimizationIgnored(pkg: String): Boolean = true
}
