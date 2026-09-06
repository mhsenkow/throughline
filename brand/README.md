# Throughline mark

Source of truth for the app icon across web, desktop, and stores.

## Idea

Three equal cells on a vertical spine — a **linear notebook**, not a node graph.
Where bars meet, an SVG metaball filter (`feGaussianBlur` + contrast
`feColorMatrix`) fuses them into goo bridges. One Braun-orange indicator marks
the active cell (kept outside the filter so it stays crisp).

## Files

| File | Role |
|---|---|
| `icon.svg` | Canonical source (light field) |
| `icon-dark.svg` | Dark-field alternate |
| `icon-1024.png` | Raster master for `cargo tauri icon` |

## Regenerate platform icons

```bash
rsvg-convert -w 1024 -h 1024 brand/icon.svg -o brand/icon-1024.png
cd desktop/src-tauri && cargo tauri icon ../../brand/icon-1024.png -o icons

# Web copies
rsvg-convert -w 180 -h 180 brand/icon.svg -o icons/apple-touch-icon.png
rsvg-convert -w 192 -h 192 brand/icon.svg -o icons/icon-192.png
rsvg-convert -w 512 -h 512 brand/icon.svg -o icons/icon-512.png
cp brand/icon.svg icons/icon.svg
cp desktop/src-tauri/icons/icon.ico icons/favicon.ico
```
