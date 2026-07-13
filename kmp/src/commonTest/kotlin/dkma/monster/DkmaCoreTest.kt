package dkma.monster

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class DkmaCoreTest {

    @Test
    fun detects_xiaomi_by_manufacturer() {
        val oem = DkmaCore.detect(DeviceInfo("Xiaomi", "Redmi"))
        assertEquals("xiaomi", oem.id)
        assertTrue(oem.steps.any { it.id == "autostart" })
    }

    @Test
    fun detects_by_brand_substring() {
        assertEquals("xiaomi", DkmaCore.detect(DeviceInfo("Foo", "POCO")).id)
        assertEquals("samsung", DkmaCore.detect(DeviceInfo("samsung", "samsung")).id)
        assertEquals("transsion",
            DkmaCore.detect(DeviceInfo("TECNO", "tecno")).id)
    }

    @Test
    fun detects_by_prop() {
        val info = DeviceInfo("unknown", "unknown",
            mapOf("ro.miui.ui.version.name" to "V14"))
        assertEquals("xiaomi", DkmaCore.detect(info).id)
    }

    @Test
    fun unknown_falls_back_to_generic() {
        val oem = DkmaCore.detect(DeviceInfo("FooBarPhone", "quux"))
        assertEquals("generic", oem.id)
        assertEquals(2, oem.steps.size)
    }

    @Test
    fun components_parse_into_pairs() {
        val xiaomi = DkmaCore.detect(DeviceInfo("Xiaomi", "Redmi"))
        val autostart = xiaomi.steps.first { it.id == "autostart" }
        val comps = DkmaCore.componentsFor(autostart, "com.your.app")
        assertTrue(comps.isNotEmpty())
        assertEquals("com.miui.securitycenter", comps.first().first)
    }

    @Test
    fun extras_substitute_pkg() {
        val xiaomi = DkmaCore.detect(DeviceInfo("Xiaomi", "Redmi"))
        val battery = xiaomi.steps.first { it.id == "battery_profile" }
        val extras = DkmaCore.extrasFor(battery, "com.your.app")
        assertEquals("com.your.app", extras["package_name"])
    }

    @Test
    fun registry_has_all_oems() {
        assertEquals(15, DkmaCore.oems.size)
        assertTrue(DkmaCore.registryVersion.isNotBlank())
    }
}
