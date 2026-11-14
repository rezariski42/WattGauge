#!/bin/sh
# Package the freshly built installer into a release zip + checksums.
set -e
cd "$(dirname "$0")/.."
VER=1.2.0
DIST=dist
rm -rf "$DIST/pkg"
mkdir -p "$DIST/pkg"
cp build/WattGauge-Setup.exe "$DIST/pkg/WattGauge-Setup-$VER.exe"
cp README.md "$DIST/pkg/README.md"
cp -r docs "$DIST/pkg/docs"
(cd "$DIST/pkg" && sha256sum "WattGauge-Setup-$VER.exe" > SHA256SUMS.txt)
rm -f "$DIST/WattGauge-$VER-win64.zip"
(cd "$DIST/pkg" && zip -qr "../WattGauge-$VER-win64.zip" .)
cp "$DIST/pkg/SHA256SUMS.txt" "$DIST/SHA256SUMS.txt"
ls -lh "$DIST/WattGauge-$VER-win64.zip"
cat "$DIST/SHA256SUMS.txt"