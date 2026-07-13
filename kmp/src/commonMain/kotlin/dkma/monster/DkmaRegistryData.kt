// -----------------------------------------------------------------------------
// GENERATED FILE -- DO NOT EDIT BY HAND.
// Source: data/oem_registry.json  (registry version 1.0.0)
// Regenerate: python3 tools/gen_kmp_registry.py
// -----------------------------------------------------------------------------
package dkma.monster

/**
 * Platform-agnostic OEM registry data for Kotlin Multiplatform (commonMain).
 * Contains no Android types; platform code turns [RegStep] into real intents.
 */
public data class RegStep(
    val id: String,
    val title: String,
    val hint: String = "",
    val components: List<String> = emptyList(),
    val use: String? = null,
    val extras: Map<String, String> = emptyMap(),
)

public data class RegOem(
    val id: String,
    val label: String,
    val manufacturer: List<String> = emptyList(),
    val brand: List<String> = emptyList(),
    val props: List<String> = emptyList(),
    val steps: List<RegStep> = emptyList(),
)

public object DkmaRegistryData {

    public const val REGISTRY_VERSION: String = "1.0.0"

    public val OEMS: List<RegOem> = listOf(
        RegOem(
            id = "xiaomi",
            label = "Xiaomi / Redmi / POCO (MIUI / HyperOS)",
            manufacturer = listOf("xiaomi"),
            brand = listOf("xiaomi", "redmi", "poco"),
            props = listOf("ro.miui.ui.version.name", "ro.mi.os.version.name"),
            steps = listOf(
                RegStep(
                    id = "autostart",
                    title = "Autostart (enable for your app)",
                    hint = "Find this app in the Autostart list and turn its toggle ON. This is the single most important step.",
                    components = listOf("com.miui.securitycenter/com.miui.permcenter.autostart.AutoStartManagementActivity", "com.miui.securitycenter/com.miui.permcenter.autostart.AutoStartManagementActivityNew")),
                RegStep(
                    id = "battery_profile",
                    title = "Battery saver -> No restrictions",
                    hint = "Set this app\u2019s battery mode to \u201cNo restrictions\u201d (not \u201cBattery saver\u201d).",
                    components = listOf("com.miui.powerkeeper/com.miui.powerkeeper.ui.HiddenAppsConfigActivity"),
                    extras = mapOf("package_name" to "%PKG%")),
                RegStep(
                    id = "app_details",
                    title = "App info (Keep running after screen off)",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "samsung",
            label = "Samsung (One UI)",
            manufacturer = listOf("samsung"),
            brand = listOf("samsung"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "sleeping_apps",
                    title = "Device care -> Battery -> Background usage limits",
                    hint = "Make sure this app is NOT in \u201cSleeping apps\u201d or \u201cDeep sleeping apps.\u201d Remove it if listed.",
                    components = listOf("com.samsung.android.lool/com.samsung.android.sm.battery.ui.BatteryActivity", "com.samsung.android.sm/com.samsung.android.sm.ui.battery.BatteryActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info -> Battery -> Unrestricted",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "huawei",
            label = "Huawei / Honor (EMUI / MagicOS)",
            manufacturer = listOf("huawei", "honor"),
            brand = listOf("huawei", "honor"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "protected_apps",
                    title = "App launch / Protected apps (set to Manage manually, all ON)",
                    hint = "Switch this app to \u201cManage manually,\u201d then enable Auto-launch, Secondary launch and Run in background.",
                    components = listOf("com.huawei.systemmanager/.startupmgr.ui.StartupNormalAppListActivity", "com.huawei.systemmanager/.optimize.process.ProtectActivity", "com.huawei.systemmanager/.optimize.bootstart.BootStartActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info -> Battery",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "oppo",
            label = "OPPO (ColorOS)",
            manufacturer = listOf("oppo"),
            brand = listOf("oppo"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "startup_manager",
                    title = "Startup manager (allow auto-launch)",
                    hint = "Allow this app to auto-launch in the Startup manager.",
                    components = listOf("com.coloros.safecenter/.startupapp.StartupAppListActivity", "com.coloros.safecenter/com.coloros.privacypermissionsentry.PermissionTopActivity", "com.oppo.safe/.permission.startup.StartupAppListActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info -> Battery",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "vivo",
            label = "vivo (Funtouch / OriginOS)",
            manufacturer = listOf("vivo"),
            brand = listOf("vivo", "iqoo"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "autostart",
                    title = "Autostart / Background power (allow)",
                    hint = "Find this app in the Autostart list and turn its toggle ON. This is the single most important step.",
                    components = listOf("com.iqoo.secure/.ui.phoneoptimize.AddWhiteListActivity", "com.iqoo.secure/.safeguard.PurviewTabActivity", "com.vivo.permissionmanager/.activity.BgStartUpManagerActivity", "com.vivo.abe/com.vivo.applicationbehaviorengine.ui.ExcessivePowerManagerActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info -> Battery",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "oneplus",
            label = "OnePlus (OxygenOS / ColorOS)",
            manufacturer = listOf("oneplus"),
            brand = listOf("oneplus"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "recent_lock",
                    title = "Recent apps -> lock the app; then Battery optimization -> Don't optimize",
                    hint = "Lock the app card in Recent apps, then set Battery optimization to \u201cDon\u2019t optimize.\u201d",
                    use = "generic.battery_optimization_list"),
                RegStep(
                    id = "chain_launch",
                    title = "Advanced optimization / Deep optimization (disable)",
                    hint = "Turn off \u201cDeep / Advanced optimization\u201d for this app.",
                    components = listOf("com.oneplus.security/.chainlaunch.view.ChainLaunchAppListActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info -> Battery",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "realme",
            label = "realme (realme UI / ColorOS)",
            manufacturer = listOf("realme"),
            brand = listOf("realme"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "startup_manager",
                    title = "Startup manager (allow auto-launch)",
                    hint = "Allow this app to auto-launch in the Startup manager.",
                    components = listOf("com.coloros.safecenter/.startupapp.StartupAppListActivity", "com.coloros.safecenter/com.coloros.privacypermissionsentry.PermissionTopActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info -> Battery",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "meizu",
            label = "Meizu (Flyme)",
            manufacturer = listOf("meizu"),
            brand = listOf("meizu"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "security",
                    title = "Security -> Permissions / Background management",
                    hint = "In the Security app, allow this app to keep running in the background.",
                    components = listOf("com.meizu.safe/.permission.SmartBGActivity", "com.meizu.safe/.permission.PermissionMainActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "asus",
            label = "ASUS (ZenUI)",
            manufacturer = listOf("asus"),
            brand = listOf("asus"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "auto_start",
                    title = "Auto-start manager / Mobile Manager",
                    hint = "Allow this app to auto-start via the device\u2019s Mobile/Phone Manager.",
                    components = listOf("com.asus.mobilemanager/.MainActivity", "com.asus.mobilemanager/.autostart.AutoStartActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "sony",
            label = "Sony (Xperia)",
            manufacturer = listOf("sony"),
            brand = listOf("sony"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "stamina",
                    title = "STAMINA mode -> exclude app; Battery optimization -> Don't optimize",
                    hint = "Add this app to the exceptions of STAMINA / battery-saver mode.",
                    use = "generic.battery_optimization_list"),
                RegStep(
                    id = "app_details",
                    title = "App info",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "nokia",
            label = "Nokia / HMD",
            manufacturer = listOf("hmd global", "nokia"),
            brand = listOf("nokia"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "battery_opt",
                    title = "Battery optimization -> Don't optimize",
                    hint = "In the battery-optimization list, set this app to \u201cDon\u2019t optimize.\u201d",
                    use = "generic.battery_optimization_list"),
                RegStep(
                    id = "app_details",
                    title = "App info",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "google",
            label = "Google Pixel / Android One (stock)",
            manufacturer = listOf("google"),
            brand = listOf("google"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "battery_opt",
                    title = "Battery optimization -> Don't optimize",
                    hint = "In the battery-optimization list, set this app to \u201cDon\u2019t optimize.\u201d",
                    use = "generic.battery_optimization_list"),
                RegStep(
                    id = "app_details",
                    title = "App info -> Battery -> Unrestricted",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "motorola",
            label = "Motorola / Lenovo (near-stock)",
            manufacturer = listOf("motorola", "lenovo"),
            brand = listOf("motorola", "lenovo"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "battery_opt",
                    title = "Battery optimization -> Don't optimize",
                    hint = "In the battery-optimization list, set this app to \u201cDon\u2019t optimize.\u201d",
                    use = "generic.battery_optimization_list"),
                RegStep(
                    id = "app_details",
                    title = "App info",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "nothing",
            label = "Nothing (Nothing OS)",
            manufacturer = listOf("nothing"),
            brand = listOf("nothing"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "battery_opt",
                    title = "Battery optimization -> Don't optimize",
                    hint = "In the battery-optimization list, set this app to \u201cDon\u2019t optimize.\u201d",
                    use = "generic.battery_optimization_list"),
                RegStep(
                    id = "app_details",
                    title = "App info -> Battery -> Unrestricted",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
        RegOem(
            id = "tecno_infinix_itel",
            label = "Transsion: Tecno / Infinix / itel (HiOS / XOS)",
            manufacturer = listOf("tecno", "infinix", "itel", "transsion"),
            brand = listOf("tecno", "infinix", "itel"),
            props = listOf(),
            steps = listOf(
                RegStep(
                    id = "autostart",
                    title = "Phone Master -> Auto-start / App freezer",
                    hint = "Find this app in the Autostart list and turn its toggle ON. This is the single most important step.",
                    components = listOf("com.transsion.phonemaster/.appaccelerate.AppFreezerActivity", "com.cxzh.antivirus/.ui.MainActivity")),
                RegStep(
                    id = "app_details",
                    title = "App info",
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d",
                    use = "generic.app_details"))),
    )

    /** The generic / stock-Android fallback profile. */
    public val GENERIC: RegOem = RegOem(
        id = "generic",
        label = "Generic / Stock Android",
        steps = listOf(
            RegStep(
                id = "battery_opt",
                title = "Battery optimization \u2192 Don't optimize",
                hint = "In the list that opens, find this app and set it to \u201cDon't optimize.\u201d",
                use = "generic.battery_optimization_list"),
            RegStep(
                id = "app_details",
                title = "App info \u2192 Battery \u2192 Unrestricted",
                hint = "Open Battery and choose \u201cUnrestricted\u201d so the app can run freely."),
        ),
    )
}
