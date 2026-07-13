package dkma.monster

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings

/**
 * DkmaMonster — universal in-app "Don't Kill My App!" helper.
 *
 * Detects the device OEM and deep-links the user to the correct autostart /
 * battery / background screens for ~15 vendor families, with graceful
 * fallbacks to generic Android screens. Zero dependencies.
 *
 * Quick start:
 *     if (DkmaMonster.needsAttention(context)) {
 *         DkmaMonster.runGuidedSetup(activity)   // opens each required screen
 *     }
 *
 * Or build your own wizard from DkmaMonster.stepsFor(context).
 */
object DkmaMonster {

    // ---- OEM model ---------------------------------------------------------

    /** One tappable step: a human title + ordered candidate components/intents. */
    data class Step(
        val id: String,
        val title: String,
        val components: List<ComponentName> = emptyList(),
        val fallbackIntent: (Context) -> Intent = ::appDetailsIntent,
        val extras: Map<String, String> = emptyMap(),
        /** Short on-screen instruction shown by the Compose wizard (optional). */
        val hint: String = "",
    )

    data class Oem(val id: String, val label: String, val steps: (Context) -> List<Step>)

    // ---- Detection ---------------------------------------------------------

    /** Exposed for the generated [DkmaRegistry] matchers. */
    internal val deviceManuf get() = Build.MANUFACTURER.lowercase()
    internal val deviceBrand get() = Build.BRAND.lowercase()

    fun currentOem(): Oem =
        DkmaRegistry.OEMS.firstOrNull { it.matches() }?.oem ?: DkmaRegistry.GENERIC

    fun romLabel(): String {
        prop("ro.mi.os.version.name").ifNotBlank { return "HyperOS $it" }
        prop("ro.miui.ui.version.name").ifNotBlank { return "MIUI $it" }
        return "${Build.MANUFACTURER} ${Build.MODEL}"
    }

    /**
     * True if the app likely needs the user's attention. Considers the
     * battery-optimization exemption on every device, and — where we can read it
     * authoritatively (MIUI/HyperOS) — whether Autostart is actually disabled.
     */
    fun needsAttention(ctx: Context): Boolean {
        if (!isIgnoringBatteryOptimizations(ctx)) return true
        return DkmaAutostart.getState(ctx) == DkmaAutostart.State.DISABLED
    }

    fun isIgnoringBatteryOptimizations(ctx: Context): Boolean {
        val pm = ctx.getSystemService(Context.POWER_SERVICE) as PowerManager
        return pm.isIgnoringBatteryOptimizations(ctx.packageName)
    }

    /**
     * Authoritative autostart state where readable (MIUI/HyperOS), else
     * [DkmaAutostart.State.UNSUPPORTED]/[UNKNOWN]. Delegates to [DkmaAutostart].
     */
    fun autostartState(ctx: Context): DkmaAutostart.State = DkmaAutostart.getState(ctx)

    // ---- Public API --------------------------------------------------------

    /** The ordered list of steps the current device needs. */
    fun stepsFor(ctx: Context): List<Step> = currentOem().steps(ctx)

    /**
     * Opens every required screen in order. Call from an Activity. Pair it with
     * your own between-step dialogs for the best UX (see README).
     */
    fun runGuidedSetup(ctx: Context) {
        requestIgnoreBatteryOptimizations(ctx)
        stepsFor(ctx).forEach { openStep(ctx, it) }
    }

    /** Ask the system to whitelist the app from Doze/battery optimization. */
    fun requestIgnoreBatteryOptimizations(ctx: Context) {
        if (isIgnoringBatteryOptimizations(ctx)) return
        val i = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
            data = Uri.parse("package:${ctx.packageName}")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        if (!start(ctx, i)) start(ctx,
            Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }

    /** Open a single step: try each component, then its fallback intent. */
    fun openStep(ctx: Context, step: Step): Boolean {
        for (comp in step.components) {
            val i = Intent().apply {
                component = comp
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                step.extras.forEach { (k, v) ->
                    putExtra(k, v.replace("%PKG%", ctx.packageName))
                }
            }
            if (start(ctx, i)) return true
        }
        return start(ctx, step.fallbackIntent(ctx))
    }

    // ---- Shared intents (used by the generated DkmaRegistry too) ------------

    internal fun appDetailsIntent(ctx: Context) =
        Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
            data = Uri.parse("package:${ctx.packageName}")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }

    internal fun batteryOptListIntent(@Suppress("UNUSED_PARAMETER") ctx: Context) =
        Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

    // ---- (OEM registry now lives in the generated DkmaRegistry.kt) ----------

    // ---- utils -------------------------------------------------------------

    private fun start(ctx: Context, intent: Intent): Boolean = try {
        if (intent.resolveActivity(ctx.packageManager) != null) {
            ctx.startActivity(intent); true
        } else false
    } catch (e: Exception) { false }

    private fun prop(key: String): String = readProp(key)

    /** Read a system property via reflection; exposed for the generated registry. */
    internal fun readProp(key: String): String = try {
        @Suppress("PrivateApi")
        val c = Class.forName("android.os.SystemProperties")
        (c.getMethod("get", String::class.java).invoke(null, key) as? String)
            ?.trim().orEmpty()
    } catch (e: Exception) { "" }

    private inline fun String.ifNotBlank(block: (String) -> Unit) {
        if (isNotBlank()) block(this)
    }
}
