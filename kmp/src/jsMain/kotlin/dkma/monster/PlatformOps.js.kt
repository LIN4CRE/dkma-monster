package dkma.monster

/**
 * JS `actual` for [PlatformOps]. In a browser/Node context there is no device to
 * inspect, so detection returns an empty signature (generic profile) and opening
 * is a no-op. Lets shared logic (detection, step lists, copy) run on JS targets.
 */
public actual object PlatformOps {

    public actual fun deviceInfo(): DeviceInfo =
        DeviceInfo(manufacturer = "", brand = "", props = emptyMap())

    public actual fun openStep(step: RegStep, pkg: String): Boolean = false

    public actual fun isBatteryOptimizationIgnored(pkg: String): Boolean = true
}
