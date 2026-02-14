# GlassDrop

GlassDrop is a GTK4/libadwaita desktop app for downloading media with `yt-dlp`.

## Features
- URL paste + auto metadata fetch
- Resolution/format selection + presets
- Queue and download history
- Daily refreshed supported-sites list
- Donation QR popup, credits, license, and disclaimer dialogs
- Flatpak packaging (`com.milas.GlassDrop`)

## Run (Python)
```bash
python3 app/main.py
```

Requirements:
- Python 3
- `PyGObject`
- `yt-dlp`

Install deps:
```bash
pip install -r requirements.txt
```

## Run (Flatpak)
Build + install:
```bash
flatpak-builder --user --install --force-clean build-dir com.milas.GlassDrop.yml
```

Run:
```bash
flatpak run com.milas.GlassDrop
```

## AppImage
Current repo includes AppImage build assets in `dist/`.

## Repository
- Homepage: https://github.com/Killersparrow1/GlassDrop
- Issues: https://github.com/Killersparrow1/GlassDrop/issues

## License
MIT
