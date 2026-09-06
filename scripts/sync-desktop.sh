#!/usr/bin/env bash
# Sync the web MVP into the Tauri frontend dist.
# Pure bash so Windows runners (Git Bash + system Python) don't choke on
# Unix-style paths passed into pathlib.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/desktop/src"
mkdir -p "$DEST/icons"
cp "$ROOT/index.html" "$DEST/index.html"
cp "$ROOT/library.json" "$DEST/library.json"
cp -R "$ROOT/icons/." "$DEST/icons/"

if ! grep -q '__THROUGHLINE_SHELL__' "$DEST/index.html"; then
  marker='<script>window.__THROUGHLINE_SHELL__="desktop";</script>'
  awk -v m="$marker" '
    !done && index($0, "<head>") {
      print
      print "  " m
      done = 1
      next
    }
    { print }
  ' "$DEST/index.html" > "$DEST/index.html.tmp"
  mv "$DEST/index.html.tmp" "$DEST/index.html"
fi
echo "synced desktop/src ← index.html + library.json"
