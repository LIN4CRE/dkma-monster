#!/usr/bin/env python3
# =============================================================================
#  DKMA MONSTER  --  Kotlin registry code generator
#  Generates android/DkmaRegistry.kt from data/oem_registry.json so the in-app
#  library shares the SAME source of truth as the CLI / GUI / web / root tools.
#  Never hand-edit DkmaRegistry.kt -- edit the JSON and re-run this.
#
#  Usage:  python3 tools/gen_kotlin_registry.py            # write the file
#          python3 tools/gen_kotlin_registry.py --check    # verify up-to-date
# =============================================================================
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "..", "data", "oem_registry.json")
OUT = os.path.join(HERE, "..", "android", "DkmaRegistry.kt")

# Map a registry "use" reference to the DkmaMonster fallback-intent function.
USE_TO_FALLBACK = {
    "generic.app_details": "::appDetailsIntent",
    "generic.battery_optimization_list": "::batteryOptListIntent",
    "generic.battery_optimization_request": "::batteryOptListIntent",
    "generic.battery_saver": "::batteryOptListIntent",
    "generic.dev_options": "::appDetailsIntent",
}


def kstr(s: str) -> str:
    """Kotlin string literal with non-ASCII emitted as \\uXXXX (ASCII-safe file)."""
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


def emit_components(comps):
    parts = []
    for c in comps:
        pkg, cls = c.split("/", 1)
        parts.append(f"cn({kstr(pkg)}, {kstr(cls)})")
    return parts


def emit_step(step, indent="                "):
    args = [kstr(step["id"]), kstr(step.get("title", step["id"]))]
    comps = step.get("components", [])
    if comps:
        joined = ("listOf(\n" + ",\n".join(
            indent + "    " + p for p in emit_components(comps)) + ")")
        args.append("components = " + joined)
    use = step.get("use")
    if use:
        fb = USE_TO_FALLBACK.get(use, "::appDetailsIntent")
        args.append("fallbackIntent = " + fb)
    extras = step.get("extras")
    if extras:
        entries = ", ".join(f"{kstr(k)} to {kstr(v)}" for k, v in extras.items())
        args.append("extras = mapOf(" + entries + ")")
    hint = step.get("hint")
    if hint:
        args.append("hint = " + kstr(hint))
    body = (",\n" + indent + "    ").join(args)
    return f"{indent}Step(\n{indent}    {body})"


def emit_oem(oem):
    steps = ",\n".join(emit_step(s) for s in oem["steps"])
    m = oem["match"]
    manuf = ", ".join(kstr(x) for x in m.get("manufacturer", []))
    brand = ", ".join(kstr(x) for x in m.get("brand", []))
    props = ", ".join(kstr(x) for x in m.get("props", []))
    matcher_args = [f"Oem({kstr(oem['id'])}, {kstr(oem['label'])}) {{ _ ->",
                    f"            listOf(\n{steps})\n        }}"]
    tail = []
    if manuf:
        tail.append(f"manuf = listOf({manuf})")
    if brand:
        tail.append(f"brand = listOf({brand})")
    if props:
        tail.append(f"props = listOf({props})")
    tail_str = (",\n           " + ",\n           ".join(tail)) if tail else ""
    return (f"        Matcher({matcher_args[0]}\n{matcher_args[1]}{tail_str}),")


def generate(reg):
    generic = None
    # GENERIC comes from the top-level generic refs -> build a stock profile.
    generic_steps = [
        {"id": "battery_opt",
         "title": "Battery optimization \u2192 Don't optimize",
         "use": "generic.battery_optimization_list",
         "hint": "In the list that opens, find this app and set it to \u201cDon't optimize.\u201d"},
        {"id": "app_details",
         "title": "App info \u2192 Battery \u2192 Unrestricted",
         "hint": "Open Battery and choose \u201cUnrestricted\u201d so the app can run freely."},
    ]
    generic_body = ",\n".join(emit_step(s, indent="            ") for s in generic_steps)

    oem_blocks = "\n".join(emit_oem(o) for o in reg["oems"])

    return f'''// -----------------------------------------------------------------------------
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
internal object DkmaRegistry {{

    class Matcher(
        val oem: Oem,
        val manuf: List<String> = emptyList(),
        val brand: List<String> = emptyList(),
        val props: List<String> = emptyList(),
    ) {{
        fun matches(): Boolean =
            manuf.any {{ DkmaMonster.deviceManuf.contains(it) }} ||
            brand.any {{ DkmaMonster.deviceBrand.contains(it) }} ||
            props.any {{ DkmaMonster.readProp(it).isNotBlank() }}
    }}

    private fun cn(pkg: String, cls: String) = ComponentName(pkg, cls)
    private fun appDetailsIntent(ctx: Context) = DkmaMonster.appDetailsIntent(ctx)
    private fun batteryOptListIntent(ctx: Context) = DkmaMonster.batteryOptListIntent(ctx)

    val GENERIC = Oem("generic", "Generic / Stock Android") {{ _ ->
        listOf(
{generic_body})
    }}

    val OEMS: List<Matcher> = listOf(
{oem_blocks}
    )
}}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the generated file is stale")
    args = ap.parse_args()

    with open(REGISTRY, encoding="utf-8") as f:
        reg = json.load(f)
    generated = generate(reg)

    if args.check:
        if not os.path.exists(OUT):
            print("DRIFT: android/DkmaRegistry.kt is missing. Run the generator.")
            return 1
        current = open(OUT, encoding="utf-8").read()
        if current != generated:
            print("DRIFT: android/DkmaRegistry.kt is out of date with the JSON.")
            print("Run: python3 tools/gen_kotlin_registry.py")
            return 1
        print("OK: DkmaRegistry.kt is in sync with oem_registry.json")
        return 0

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(generated)
    print(f"Generated {os.path.relpath(OUT)} "
          f"({len(reg['oems'])} OEMs, "
          f"{sum(len(o['steps']) for o in reg['oems'])} steps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
