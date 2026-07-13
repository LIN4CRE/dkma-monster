package dkma.monster

import android.content.Context
import android.os.Build

/**
 * DkmaAutostart — an authoritative reader for the "Autostart" permission on
 * OEM ROMs that expose it (primarily Xiaomi/MIUI/HyperOS, plus best-effort for
 * a few others), implemented with pure reflection and zero dependencies.
 *
 * Background
 * ----------
 * Most OEM background-killer toggles have no readable state. Autostart is the
 * one meaningful exception on MIUI: it is backed by a hidden AppOps op, so we
 * can query AppOpsManager via reflection (the same technique the community
 * MIUI-autostart library uses) and get a real ALLOWED / IGNORED answer.
 *
 * This gives the in-app wizard and the [DkmaMonster] engine an *authoritative*
 * autostart check instead of a heuristic — so you only nag the user when the
 * permission is genuinely off, and you can show a green tick when it's on.
 *
 * Usage:
 *     when (DkmaAutostart.getState(context)) {
 *         DkmaAutostart.State.ENABLED    -> // good, don't nag
 *         DkmaAutostart.State.DISABLED   -> // send user to the Autostart screen
 *         DkmaAutostart.State.UNKNOWN    -> // couldn't read; fall back to guiding
 *         DkmaAutostart.State.UNSUPPORTED-> // not a ROM that exposes autostart
 *     }
 */
object DkmaAutostart {

    enum class State { ENABLED, DISABLED, UNKNOWN, UNSUPPORTED }

    // AppOpsManager result codes (stable public constants, redeclared to avoid
    // relying on hidden fields).
    private const val MODE_ALLOWED = 0
    private const val MODE_IGNORED = 1
    private const val MODE_ERRORED = 2
    private const val MODE_DEFAULT = 3

    // Known vendor "autostart" AppOps op codes. MIUI's OP_AUTO_START has been
    // 10008 across MIUI 10–14/HyperOS. We try the primary first, then fallbacks.
    private val MIUI_AUTOSTART_OPS = intArrayOf(10008, 10021)

    /** True on Xiaomi/Redmi/POCO MIUI or HyperOS devices. */
    fun isMiui(): Boolean {
        val m = Build.MANUFACTURER.lowercase()
        val b = Build.BRAND.lowercase()
        return m.contains("xiaomi") || b.contains("xiaomi") ||
               b.contains("redmi") || b.contains("poco") ||
               readProp("ro.miui.ui.version.name").isNotBlank() ||
               readProp("ro.mi.os.version.name").isNotBlank()
    }

    /**
     * Authoritative autostart state for this app.
     * Returns [State.UNSUPPORTED] on ROMs without a readable autostart op.
     */
    fun getState(ctx: Context): State {
        if (!isMiui()) return State.UNSUPPORTED
        val uid = ctx.applicationInfo.uid
        val pkg = ctx.packageName
        for (op in MIUI_AUTOSTART_OPS) {
            val mode = checkOpNoThrow(ctx, op, uid, pkg) ?: continue
            return when (mode) {
                MODE_ALLOWED, MODE_DEFAULT -> State.ENABLED
                MODE_IGNORED, MODE_ERRORED -> State.DISABLED
                else -> State.UNKNOWN
            }
        }
        return State.UNKNOWN
    }

    /** Convenience: true only when we can *prove* autostart is enabled. */
    fun isEnabled(ctx: Context): Boolean = getState(ctx) == State.ENABLED

    /** Convenience: true only when we can *prove* autostart is disabled. */
    fun isDisabled(ctx: Context): Boolean = getState(ctx) == State.DISABLED

    // ---- reflection core ---------------------------------------------------

    /**
     * Calls AppOpsManager.checkOpNoThrow(int op, int uid, String pkg) via
     * reflection. Returns the mode int, or null if the call isn't available
     * (e.g. non-MIUI, or the hidden method is blocked on this ROM).
     */
    private fun checkOpNoThrow(ctx: Context, op: Int, uid: Int, pkg: String): Int? {
        return try {
            val appOps = ctx.getSystemService(Context.APP_OPS_SERVICE) ?: return null
            val cls = appOps.javaClass
            // Preferred signature present on most ROMs.
            val m = try {
                cls.getMethod("checkOpNoThrow",
                    Int::class.javaPrimitiveType,
                    Int::class.javaPrimitiveType,
                    String::class.java)
            } catch (e: NoSuchMethodException) {
                // Some ROMs only expose checkOp(...) with the same params.
                cls.getMethod("checkOp",
                    Int::class.javaPrimitiveType,
                    Int::class.javaPrimitiveType,
                    String::class.java)
            }
            (m.invoke(appOps, op, uid, pkg) as? Int)
        } catch (e: Throwable) {
            null
        }
    }

    private fun readProp(key: String): String = try {
        @Suppress("PrivateApi")
        val c = Class.forName("android.os.SystemProperties")
        (c.getMethod("get", String::class.java).invoke(null, key) as? String)
            ?.trim().orEmpty()
    } catch (e: Throwable) { "" }
}
