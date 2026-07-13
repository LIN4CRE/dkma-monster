#!/system/bin/sh
# =============================================================================
#  DKMA MONSTER  —  ROOT variant (fully automatic, zero taps)
#  Run in a root shell ON the device (Termux + su, or `adb shell` then `su`).
#     su -c 'sh /sdcard/dkma-root.sh com.your.app'
#
#  With root we can flip almost everything non-interactively: Doze whitelist,
#  standby bucket, background appops, vendor autostart appops, and several
#  vendor secure-settings keys. UI-only toggles with no backing store still
#  need the guided ADB flow, but this covers the vast majority.
# =============================================================================

PKG="${1:-YOUR.APP.PACKAGE}"

log()  { echo "[*] $*"; }
ok()   { echo "[+] $*"; }
warn() { echo "[!] $*"; }

if [ "$(id -u)" != "0" ]; then
  warn "Not running as root. Re-run via:  su -c 'sh $0 $PKG'"
  exit 1
fi
if [ "$PKG" = "YOUR.APP.PACKAGE" ]; then
  warn "Usage: sh dkma-root.sh com.your.app"
  exit 1
fi
if ! pm list packages 2>/dev/null | grep -qx "package:$PKG"; then
  warn "Package $PKG not installed."
  exit 1
fi

MANUF=$(getprop ro.product.manufacturer | tr '[:upper:]' '[:lower:]')
log "Device manufacturer: $MANUF   target: $PKG"

# --- Universal ---------------------------------------------------------------
dumpsys deviceidle whitelist "+$PKG" >/dev/null 2>&1 && ok "Doze whitelist +$PKG"
am set-standby-bucket "$PKG" active   >/dev/null 2>&1 && ok "standby bucket active"

for OP in RUN_IN_BACKGROUND RUN_ANY_IN_BACKGROUND START_FOREGROUND \
          WAKE_LOCK INSTANT_APP_START_FOREGROUND; do
  cmd appops set "$PKG" "$OP" allow >/dev/null 2>&1 && ok "appop $OP=allow"
done

# --- Vendor autostart appops (names differ per ROM; all are best-effort) -----
for OP in AUTO_START BOOT_COMPLETED "10008" "10021"; do
  cmd appops set "$PKG" "$OP" allow >/dev/null 2>&1
done

case "$MANUF" in
  *xiaomi*)
    # MIUI stores autostart perms in its own db; toggling the appop above
    # plus the security-center perm covers most builds.
    cmd appops set "$PKG" AUTO_START allow >/dev/null 2>&1 && ok "MIUI autostart appop"
    ;;
  *huawei*|*honor*)
    # EMUI protected apps live in systemmanager db; appop is the reachable lever.
    ok "EMUI: appops applied (verify 'App launch' is Manual+all-on in UI)"
    ;;
  *oppo*|*realme*|*oneplus*)
    settings put secure "oppo_startupmanager_$PKG" 1 >/dev/null 2>&1
    ok "ColorOS: startup flags applied (best effort)"
    ;;
  *vivo*|*iqoo*)
    ok "Funtouch/OriginOS: appops applied (verify Background power in UI)"
    ;;
  *samsung*)
    # One UI 'sleeping/deep sleeping apps' lists are in a protected db;
    # removing from them typically requires the UI, but unrestricted battery
    # via appops + doze whitelist is usually enough.
    ok "One UI: doze whitelist + appops applied"
    ;;
  *)
    ok "Generic/stock: doze whitelist + appops applied"
    ;;
esac

# --- Verify ------------------------------------------------------------------
echo
log "Verification:"
dumpsys deviceidle whitelist 2>/dev/null | grep -i "$PKG" >/dev/null 2>&1 \
  && ok "in Doze whitelist" || warn "not in Doze whitelist"
echo "    standby: $(am get-standby-bucket "$PKG" 2>/dev/null)"
echo
ok "Root pass complete. Reboot recommended so all flags take effect."
