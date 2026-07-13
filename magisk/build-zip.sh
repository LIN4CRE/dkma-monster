#!/usr/bin/env bash
# Build a flashable Magisk zip from this folder.
set -e
cd "$(dirname "$0")"
OUT="../dkma-monster-magisk.zip"
rm -f "$OUT"
zip -r "$OUT" . -x "build-zip.sh" >/dev/null
echo "Built $OUT"
