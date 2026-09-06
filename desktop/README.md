# Throughline Desktop

Free forever. Same library as the web — powers the browser can't have.

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

## Release builds

Targets in `src-tauri/tauri.conf.json`: **macOS** (`.dmg` / `.app`), **Windows**
(NSIS `.exe`), **Linux** (`.deb` + `.AppImage`). Tauri only emits installers for
the OS you are on — use GitHub Actions for the other two.

### Local (this Mac → signed DMG)

```bash
./scripts/sync-desktop.sh
cd desktop
cargo tauri build
# → src-tauri/target/release/bundle/dmg/*.dmg
# → src-tauri/target/release/bundle/macos/*.app
```

`signingIdentity` is set to **Developer ID Application: Michael Senkow
(WC44W2QVE4)**. That signs the app. To also **notarize** (Gatekeeper quiet for
downloaders), export once then rebuild:

```bash
export APPLE_ID='you@example.com'
export APPLE_PASSWORD='app-specific-password'   # appleid.apple.com → App-Specific Passwords
export APPLE_TEAM_ID='WC44W2QVE4'
cd desktop && cargo tauri build
```

Or store a notary profile and let the CLI pick it up later:

```bash
xcrun notarytool store-credentials "throughline" \
  --apple-id "$APPLE_ID" --team-id WC44W2QVE4 --password "$APPLE_PASSWORD"
```

### All platforms (CI)

Push a version tag, or run **Actions → Desktop release → Run workflow**:

```bash
git tag v0.1.1 && git push origin v0.1.1
```

Workflow: [`.github/workflows/desktop-release.yml`](../.github/workflows/desktop-release.yml)

| Artifact | Runner |
|---|---|
| `Throughline_*_aarch64.dmg` | macOS 14 |
| `Throughline_*_x64.dmg` | macOS 13 |
| `Throughline_*_x64-setup.exe` | Windows |
| `Throughline_*.deb` / `.AppImage` | Ubuntu 22.04 |

Publishes a **draft** GitHub Release on `mhsenkow/throughline`. Attachments land
at https://github.com/mhsenkow/throughline/releases/latest once you publish.

Optional repo secrets for notarized macOS CI builds: `APPLE_ID`,
`APPLE_PASSWORD`, `APPLE_TEAM_ID`, `APPLE_SIGNING_IDENTITY`, and (for hosted
runners) `APPLE_CERTIFICATE` + `APPLE_CERTIFICATE_PASSWORD` (base64 `.p12`).

Windows/Linux ship **unsigned** unless you add a separate code-signing cert —
SmartScreen / desktop environments may warn once; that is expected for free
distribution.

### “Damaged and can’t be opened”

Only happens on **unsigned** or **un-notarized** downloads. After signing +
notarization, delete this workaround from your muscle memory. Until then:

```bash
xattr -cr /Applications/Throughline.app && open /Applications/Throughline.app
```
