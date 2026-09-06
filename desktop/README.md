# Throughline Desktop

Free forever. Same library as the web — powers the browser cannot have.

## What desktop unlocks

1. **Every provider / company gateway** — native HTTP, no CORS
2. **Notebooks on disk** — `~/Documents/Throughline/`
3. **OS keychain** for API keys

## Dev

```bash
# from repo root
./scripts/sync-desktop.sh
cd desktop
cargo tauri dev
```

## Release build (macOS)

```bash
./scripts/sync-desktop.sh
cd desktop
cargo tauri build
# → src-tauri/target/release/bundle/dmg/*.dmg
# → src-tauri/target/release/bundle/macos/*.app
```

Publish the `.dmg` to GitHub Releases (`throughline` repo). The website already
links to `https://github.com/mhsenkow/throughline/releases/latest`.

### “Damaged and can’t be opened”

Unsigned downloads get a quarantine flag; macOS often lies and says *damaged*.
After installing to Applications:

```bash
xattr -cr /Applications/Throughline.app && open /Applications/Throughline.app
```

Apple Developer ID + notarization will remove this for users later.
