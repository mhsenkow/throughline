#!/usr/bin/env bash
# Sync the web MVP into the Tauri frontend dist.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/desktop/src"
mkdir -p "$DEST"
cp "$ROOT/index.html" "$DEST/index.html"
cp "$ROOT/library.json" "$DEST/library.json"
python3 - <<PY
from pathlib import Path
p = Path(r"$DEST") / "index.html"
html = p.read_text(encoding="utf-8")
marker = '<script>window.__THROUGHLINE_SHELL__="desktop";</script>'
if "__THROUGHLINE_SHELL__" not in html:
    html = html.replace("<head>", "<head>\\n  " + marker, 1)
    p.write_text(html, encoding="utf-8")
print("synced desktop/src ← index.html + library.json")
PY
