package dkma.monster

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings

/**
 * Android `actual` for [PlatformOps]. Requires an application [Context], set once
 * at startup via [DkmaAndroid.init] (e.g. in your Application.onCreate).
 */
public object DkmaAndroid {
    internal lateinit var appContext: Context
    public fun init(context: Context) { appContext = context.applicationContext }
}

public actual object PlatformOps {

    public actual fun deviceInfo(): DeviceInfo {
        val props = buildMap {
            for (key in listOf("ro.miui.ui.version.name", "ro.mi.os.version.name")) {
                val v = readProp(key)
                if (v.isNotBlank()) put(key, v)
            }
        }
        return DeviceInfo(
            manufacturer = Build.MANUFACTURER ?: "",
            brand = Build.BRAND ?: "",
            props = props,
        )
    }

    public actual fun openStep(step: RegStep, pkg: String): Boolean {
        val ctx = DkmaAndroid.appContext
        // Try each candidate component in order.
        for ((cpkg, cls) in DkmaCore.componentsFor(step, pkg)) {
            val i = Intent().apply {
                component = ComponentName(cpkg, cls)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                DkmaCore.extrasFor(step, pkg).forEach { (k, v) -> putExtra(k, v) }
            }
            if (start(ctx, i)) return true
        }
        // Fall back based on the step's `use` reference, else app details.
        val fallback = when (step.use) {
            "generic.battery_optimization_list" ->
                Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            else -> appDetails(ctx, pkg)
        }
        return start(ctx, fallback)
    }

    public actual fun isBatteryOptimizationIgnored(pkg: String): Boolean {
        val pm = DkmaAndroid.appContext
            .getSystemService(Context.POWER_SERVICE) as PowerManager
        return pm.isIgnoringBatteryOptimizations(pkg)
    }

    private fun appDetails(ctx: Context, pkg: String) =
        Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
            data = Uri.parse("package:$pkg")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }

    private fun start(ctx: Context, intent: Intent): Boolean = try {
        if (intent.resolveActivity(ctx.packageManager) != null) {
            ctx.startActivity(intent); true
        } else false
    } catch (e: Exception) { false }

    private fun readProp(key: String): String = try {
        @Suppress("PrivateApi")
        val c = Class.forName("android.os.SystemProperties")
        (c.getMethod("get", String::class.java).invoke(null, key) as? String)
            ?.trim().orEmpty()
    } catch (e: Exception) { "" }
}
