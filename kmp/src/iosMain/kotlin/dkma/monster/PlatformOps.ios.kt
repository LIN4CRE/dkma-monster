package dkma.monster

/**
 * iOS `actual` for [PlatformOps]. iOS has no aggressive OEM background killers
 * and no equivalent settings screens, so detection returns an Apple signature
 * (which maps to the generic profile) and opening is a no-op. Provided so shared
 * code compiles and behaves sensibly on iOS targets.
 */
public actual object PlatformOps {

    public actual fun deviceInfo(): DeviceInfo =
        DeviceInfo(manufacturer = "Apple", brand = "Apple", props = emptyMap())

    public actual fun openStep(step: RegStep, pkg: String): Boolean = false

    public actual fun isBatteryOptimizationIgnored(pkg: String): Boolean = true
}
