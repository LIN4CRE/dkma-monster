// -----------------------------------------------------------------------------
// GENERATED FILE -- DO NOT EDIT BY HAND.
// Source: data/oem_registry.json
// Regenerate: python3 tools/gen_kotlin_registry.py
// -----------------------------------------------------------------------------
package dkma.monster

import android.content.ComponentName
import android.content.Context
import android.content.Intent

import dkma.monster.DkmaMonster.Oem
import dkma.monster.DkmaMonster.Step

/**
 * The OEM registry, generated from the JSON single source of truth. Consumed by
 * [DkmaMonster]. Each Matcher pairs an [Oem] with the manufacturer/brand/prop
 * signatures that identify it.
 */
internal object DkmaRegistry {

    class Matcher(
        val oem: Oem,
        val manuf: List<String> = emptyList(),
        val brand: List<String> = emptyList(),
        val props: List<String> = emptyList(),
    ) {
        fun matches(): Boolean =
            manuf.any { DkmaMonster.deviceManuf.contains(it) } ||
            brand.any { DkmaMonster.deviceBrand.contains(it) } ||
            props.any { DkmaMonster.readProp(it).isNotBlank() }
    }

    private fun cn(pkg: String, cls: String) = ComponentName(pkg, cls)
    private fun appDetailsIntent(ctx: Context) = DkmaMonster.appDetailsIntent(ctx)
    private fun batteryOptListIntent(ctx: Context) = DkmaMonster.batteryOptListIntent(ctx)

    val GENERIC = Oem("generic", "Generic / Stock Android") { _ ->
        listOf(
            Step(
                "battery_opt",
                "Battery optimization \u2192 Don't optimize",
                fallbackIntent = ::batteryOptListIntent,
                hint = "In the list that opens, find this app and set it to \u201cDon't optimize.\u201d"),
            Step(
                "app_details",
                "App info \u2192 Battery \u2192 Unrestricted",
                hint = "Open Battery and choose \u201cUnrestricted\u201d so the app can run freely."))
    }

    val OEMS: List<Matcher> = listOf(
        Matcher(Oem("xiaomi", "Xiaomi / Redmi / POCO (MIUI / HyperOS)") { _ ->
            listOf(
                Step(
                    "autostart",
                    "Autostart (enable for your app)",
                    components = listOf(
                    cn("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity"),
                    cn("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivityNew")),
                    hint = "Find this app in the Autostart list and turn its toggle ON. This is the single most important step."),
                Step(
                    "battery_profile",
                    "Battery saver -> No restrictions",
                    components = listOf(
                    cn("com.miui.powerkeeper", "com.miui.powerkeeper.ui.HiddenAppsConfigActivity")),
                    extras = mapOf("package_name" to "%PKG%"),
                    hint = "Set this app\u2019s battery mode to \u201cNo restrictions\u201d (not \u201cBattery saver\u201d)."),
                Step(
                    "app_details",
                    "App info (Keep running after screen off)",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("xiaomi"),
           brand = listOf("xiaomi", "redmi", "poco"),
           props = listOf("ro.miui.ui.version.name", "ro.mi.os.version.name")),
        Matcher(Oem("samsung", "Samsung (One UI)") { _ ->
            listOf(
                Step(
                    "sleeping_apps",
                    "Device care -> Battery -> Background usage limits",
                    components = listOf(
                    cn("com.samsung.android.lool", "com.samsung.android.sm.battery.ui.BatteryActivity"),
                    cn("com.samsung.android.sm", "com.samsung.android.sm.ui.battery.BatteryActivity")),
                    hint = "Make sure this app is NOT in \u201cSleeping apps\u201d or \u201cDeep sleeping apps.\u201d Remove it if listed."),
                Step(
                    "app_details",
                    "App info -> Battery -> Unrestricted",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("samsung"),
           brand = listOf("samsung")),
        Matcher(Oem("huawei", "Huawei / Honor (EMUI / MagicOS)") { _ ->
            listOf(
                Step(
                    "protected_apps",
                    "App launch / Protected apps (set to Manage manually, all ON)",
                    components = listOf(
                    cn("com.huawei.systemmanager", ".startupmgr.ui.StartupNormalAppListActivity"),
                    cn("com.huawei.systemmanager", ".optimize.process.ProtectActivity"),
                    cn("com.huawei.systemmanager", ".optimize.bootstart.BootStartActivity")),
                    hint = "Switch this app to \u201cManage manually,\u201d then enable Auto-launch, Secondary launch and Run in background."),
                Step(
                    "app_details",
                    "App info -> Battery",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("huawei", "honor"),
           brand = listOf("huawei", "honor")),
        Matcher(Oem("oppo", "OPPO (ColorOS)") { _ ->
            listOf(
                Step(
                    "startup_manager",
                    "Startup manager (allow auto-launch)",
                    components = listOf(
                    cn("com.coloros.safecenter", ".startupapp.StartupAppListActivity"),
                    cn("com.coloros.safecenter", "com.coloros.privacypermissionsentry.PermissionTopActivity"),
                    cn("com.oppo.safe", ".permission.startup.StartupAppListActivity")),
                    hint = "Allow this app to auto-launch in the Startup manager."),
                Step(
                    "app_details",
                    "App info -> Battery",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("oppo"),
           brand = listOf("oppo")),
        Matcher(Oem("vivo", "vivo (Funtouch / OriginOS)") { _ ->
            listOf(
                Step(
                    "autostart",
                    "Autostart / Background power (allow)",
                    components = listOf(
                    cn("com.iqoo.secure", ".ui.phoneoptimize.AddWhiteListActivity"),
                    cn("com.iqoo.secure", ".safeguard.PurviewTabActivity"),
                    cn("com.vivo.permissionmanager", ".activity.BgStartUpManagerActivity"),
                    cn("com.vivo.abe", "com.vivo.applicationbehaviorengine.ui.ExcessivePowerManagerActivity")),
                    hint = "Find this app in the Autostart list and turn its toggle ON. This is the single most important step."),
                Step(
                    "app_details",
                    "App info -> Battery",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("vivo"),
           brand = listOf("vivo", "iqoo")),
        Matcher(Oem("oneplus", "OnePlus (OxygenOS / ColorOS)") { _ ->
            listOf(
                Step(
                    "recent_lock",
                    "Recent apps -> lock the app; then Battery optimization -> Don't optimize",
                    fallbackIntent = ::batteryOptListIntent,
                    hint = "Lock the app card in Recent apps, then set Battery optimization to \u201cDon\u2019t optimize.\u201d"),
                Step(
                    "chain_launch",
                    "Advanced optimization / Deep optimization (disable)",
                    components = listOf(
                    cn("com.oneplus.security", ".chainlaunch.view.ChainLaunchAppListActivity")),
                    hint = "Turn off \u201cDeep / Advanced optimization\u201d for this app."),
                Step(
                    "app_details",
                    "App info -> Battery",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("oneplus"),
           brand = listOf("oneplus")),
        Matcher(Oem("realme", "realme (realme UI / ColorOS)") { _ ->
            listOf(
                Step(
                    "startup_manager",
                    "Startup manager (allow auto-launch)",
                    components = listOf(
                    cn("com.coloros.safecenter", ".startupapp.StartupAppListActivity"),
                    cn("com.coloros.safecenter", "com.coloros.privacypermissionsentry.PermissionTopActivity")),
                    hint = "Allow this app to auto-launch in the Startup manager."),
                Step(
                    "app_details",
                    "App info -> Battery",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("realme"),
           brand = listOf("realme")),
        Matcher(Oem("meizu", "Meizu (Flyme)") { _ ->
            listOf(
                Step(
                    "security",
                    "Security -> Permissions / Background management",
                    components = listOf(
                    cn("com.meizu.safe", ".permission.SmartBGActivity"),
                    cn("com.meizu.safe", ".permission.PermissionMainActivity")),
                    hint = "In the Security app, allow this app to keep running in the background."),
                Step(
                    "app_details",
                    "App info",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("meizu"),
           brand = listOf("meizu")),
        Matcher(Oem("asus", "ASUS (ZenUI)") { _ ->
            listOf(
                Step(
                    "auto_start",
                    "Auto-start manager / Mobile Manager",
                    components = listOf(
                    cn("com.asus.mobilemanager", ".MainActivity"),
                    cn("com.asus.mobilemanager", ".autostart.AutoStartActivity")),
                    hint = "Allow this app to auto-start via the device\u2019s Mobile/Phone Manager."),
                Step(
                    "app_details",
                    "App info",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("asus"),
           brand = listOf("asus")),
        Matcher(Oem("sony", "Sony (Xperia)") { _ ->
            listOf(
                Step(
                    "stamina",
                    "STAMINA mode -> exclude app; Battery optimization -> Don't optimize",
                    fallbackIntent = ::batteryOptListIntent,
                    hint = "Add this app to the exceptions of STAMINA / battery-saver mode."),
                Step(
                    "app_details",
                    "App info",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("sony"),
           brand = listOf("sony")),
        Matcher(Oem("nokia", "Nokia / HMD") { _ ->
            listOf(
                Step(
                    "battery_opt",
                    "Battery optimization -> Don't optimize",
                    fallbackIntent = ::batteryOptListIntent,
                    hint = "In the battery-optimization list, set this app to \u201cDon\u2019t optimize.\u201d"),
                Step(
                    "app_details",
                    "App info",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("hmd global", "nokia"),
           brand = listOf("nokia")),
        Matcher(Oem("google", "Google Pixel / Android One (stock)") { _ ->
            listOf(
                Step(
                    "battery_opt",
                    "Battery optimization -> Don't optimize",
                    fallbackIntent = ::batteryOptListIntent,
                    hint = "In the battery-optimization list, set this app to \u201cDon\u2019t optimize.\u201d"),
                Step(
                    "app_details",
                    "App info -> Battery -> Unrestricted",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("google"),
           brand = listOf("google")),
        Matcher(Oem("motorola", "Motorola / Lenovo (near-stock)") { _ ->
            listOf(
                Step(
                    "battery_opt",
                    "Battery optimization -> Don't optimize",
                    fallbackIntent = ::batteryOptListIntent,
                    hint = "In the battery-optimization list, set this app to \u201cDon\u2019t optimize.\u201d"),
                Step(
                    "app_details",
                    "App info",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("motorola", "lenovo"),
           brand = listOf("motorola", "lenovo")),
        Matcher(Oem("nothing", "Nothing (Nothing OS)") { _ ->
            listOf(
                Step(
                    "battery_opt",
                    "Battery optimization -> Don't optimize",
                    fallbackIntent = ::batteryOptListIntent,
                    hint = "In the battery-optimization list, set this app to \u201cDon\u2019t optimize.\u201d"),
                Step(
                    "app_details",
                    "App info -> Battery -> Unrestricted",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("nothing"),
           brand = listOf("nothing")),
        Matcher(Oem("tecno_infinix_itel", "Transsion: Tecno / Infinix / itel (HiOS / XOS)") { _ ->
            listOf(
                Step(
                    "autostart",
                    "Phone Master -> Auto-start / App freezer",
                    components = listOf(
                    cn("com.transsion.phonemaster", ".appaccelerate.AppFreezerActivity"),
                    cn("com.cxzh.antivirus", ".ui.MainActivity")),
                    hint = "Find this app in the Autostart list and turn its toggle ON. This is the single most important step."),
                Step(
                    "app_details",
                    "App info",
                    fallbackIntent = ::appDetailsIntent,
                    hint = "Open Battery and choose \u201cUnrestricted\u201d / \u201cKeep running after screen off.\u201d"))
        },
           manuf = listOf("tecno", "infinix", "itel", "transsion"),
           brand = listOf("tecno", "infinix", "itel")),
    )
}
