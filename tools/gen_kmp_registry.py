#!/usr/bin/env python3
# =============================================================================
#  DKMA MONSTER  --  Kotlin Multiplatform registry generator
#  Generates kmp/src/commonMain/.../DkmaRegistryData.kt from oem_registry.json.
#  This is PURE, platform-agnostic Kotlin (no android imports) usable from
#  commonMain across Android / iOS / JVM / JS. Never hand-edit the output.
#
#  Usage:  python3 tools/gen_kmp_registry.py            # write the file
#          python3 tools/gen_kmp_registry.py --check    # verify up to date
# =============================================================================
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "..", "data", "oem_registry.json")
OUT = os.path.join(HERE, "..", "kmp", "src", "commonMain", "kotlin",
                   "dkma", "monster", "DkmaRegistryData.kt")


def kstr(s: str) -> str:
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "$":
            out.append("\\$")
        elif ch == "\n":
            out.append("\\n")
        elif 32 <= o < 127:
            out.append(ch)
        else:
            out.append(f"\\u{o:04x}")
    out.append('"')
    return "".join(out)


def klist(items):
    return "listOf(" + ", ".join(kstr(x) for x in items) + ")"


def emit_step(s, indent="                "):
    fields = [
        f"id = {kstr(s.get('id',''))}",
        f"title = {kstr(s.get('title', s.get('id','')))}",
    ]
    if s.get("hint"):
        fields.append(f"hint = {kstr(s['hint'])}")
    if s.get("components"):
        fields.append("components = " + klist(s["components"]))
    if s.get("use"):
        fields.append(f"use = {kstr(s['use'])}")
    if s.get("extras"):
        entries = ", ".join(f"{kstr(k)} to {kstr(v)}"
                            for k, v in s["extras"].items())
        fields.append("extras = mapOf(" + entries + ")")
    body = (",\n" + indent + "    ").join(fields)
    return f"{indent}RegStep(\n{indent}    {body})"


def emit_oem(o):
    steps = ",\n".join(emit_step(s) for s in o["steps"])
    m = o["match"]
    fields = [
        f"id = {kstr(o['id'])}",
        f"label = {kstr(o['label'])}",
        f"manufacturer = {klist(m.get('manufacturer', []))}",
        f"brand = {klist(m.get('brand', []))}",
        f"props = {klist(m.get('props', []))}",
        f"steps = listOf(\n{steps})",
    ]
    body = (",\n            ").join(fields)
    return f"        RegOem(\n            {body}),"


def generate(reg):
    oem_blocks = "\n".join(emit_oem(o) for o in reg["oems"])
    version = reg.get("_meta", {}).get("version", "0")
    return f'''// -----------------------------------------------------------------------------
// GENERATED FILE -- DO NOT EDIT BY HAND.
// Source: data/oem_registry.json  (registry version {version})
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

public object DkmaRegistryData {{

    public const val REGISTRY_VERSION: String = {kstr(version)}

    public val OEMS: List<RegOem> = listOf(
{oem_blocks}
    )

    /** The generic / stock-Android fallback profile. */
    public val GENERIC: RegOem = RegOem(
        id = "generic",
        label = "Generic / Stock Android",
        steps = listOf(
            RegStep(
                id = "battery_opt",
                title = "Battery optimization \\u2192 Don't optimize",
                hint = "In the list that opens, find this app and set it to \\u201cDon't optimize.\\u201d",
                use = "generic.battery_optimization_list"),
            RegStep(
                id = "app_details",
                title = "App info \\u2192 Battery \\u2192 Unrestricted",
                hint = "Open Battery and choose \\u201cUnrestricted\\u201d so the app can run freely."),
        ),
    )
}}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    with open(REGISTRY, encoding="utf-8") as f:
        reg = json.load(f)
    generated = generate(reg)

    if args.check:
        if not os.path.exists(OUT):
            print("DRIFT: KMP DkmaRegistryData.kt is missing. Run the generator.")
            return 1
        if open(OUT, encoding="utf-8").read() != generated:
            print("DRIFT: KMP DkmaRegistryData.kt is out of date with the JSON.")
            print("Run: python3 tools/gen_kmp_registry.py")
            return 1
        print("OK: KMP DkmaRegistryData.kt is in sync with oem_registry.json")
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(generated)
    print(f"Generated {os.path.relpath(OUT)} "
          f"({len(reg['oems'])} OEMs, "
          f"{sum(len(o['steps']) for o in reg['oems'])} steps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
