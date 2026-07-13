# Contributing — add an OEM or fix a component name

The single most useful contribution is **accurate vendor Activity names** for new
ROM versions. Here's the whole workflow.

## 1. Find the real Activity on a device

With the vendor screen open on the phone:
```bash
adb shell dumpsys activity activities | grep -i mResumedActivity
# or, watch what launches:
adb shell dumpsys window | grep -i mCurrentFocus
```
Copy the `package/activity` string.

## 2. Add it to the registry

Edit `data/oem_registry.json`. Add (or extend) an entry under `oems`:
```json
{
  "id": "yourvendor",
  "label": "Your Vendor (Your UI)",
  "match": { "manufacturer": ["yourvendor"], "brand": ["yourvendor"], "props": [] },
  "steps": [
    { "id": "autostart", "title": "Autostart -> enable app",
      "components": ["com.vendor.security/.SomeAutoStartActivity"] },
    { "id": "app_details", "title": "App info", "use": "generic.app_details" }
  ],
  "root_ops": []
}
```
- List **multiple** components (newest first) — tools try each in order.
- Use `"use": "generic.xxx"` to reuse a shared intent instead of a component.
- `%PKG%` in `data`/`extras` is replaced with the target package at runtime.

## 3. Regenerate the derived artifacts (do NOT hand-edit them)

The in-app Kotlin registry and the web dashboard are **generated** from the JSON:

```bash
python3 tools/build_all.py
```

This rewrites `android/DkmaRegistry.kt` and `web/site/` from your edit. Commit the
JSON **and** the regenerated files. CI runs `python3 tools/build_all.py --check`
and fails if they're out of sync. Never edit `DkmaRegistry.kt` by hand — it has a
"GENERATED — DO NOT EDIT" header.

<details><summary>(Legacy note) the app used to hand-mirror the registry</summary>

Older versions kept a matching `Matcher(Oem(...))` block in `DkmaMonster.kt`. That
is now generated, so this manual step no longer exists.
</details>

## 4. Test detection without a device
```bash
python3 - <<'PY'
import importlib.util
s=importlib.util.spec_from_file_location("d","adb/dkma.py")
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
reg=m.load_registry()
print(m.detect_oem(reg,"YourVendor","yourvendor",{}))
PY
```

## 5. Test on-device
```bash
python3 adb/dkma.py com.your.app
```
Confirm each screen opens. If a component fails on a ROM, add its replacement to
the front of the `components` list — don't remove the old one (other ROMs need it).

## Style
- Keep component lists ordered newest → oldest.
- Prefer additive changes; never delete a working fallback.
- One OEM family per registry entry; group sub-brands via `match` arrays.
