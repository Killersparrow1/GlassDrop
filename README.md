<p align="center">
  <img src="app/assets/GlassDrop.png" alt="GlassDrop Logo" width="160" />
</p>

<h1 align="center">GlassDrop</h1>

<p align="center">
  GTK4/libadwaita desktop downloader powered by <code>yt-dlp</code>.
  <br />
  Available as Python app, Flatpak, and AppImage.
</p>

## Features
- URL paste + auto metadata fetch
- Resolution/format selection + presets
- Queue and download history
- Daily refreshed supported-sites list
- Donation QR popup, credits, license, and disclaimer dialogs
- Flatpak packaging (`com.milas.GlassDrop`)

## Requirements
- Linux desktop
- Python `3.10+`
- `PyGObject`
- `yt-dlp`

## Installation (Python)
Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run:
```bash
python3 app/main.py
```

## Installation (Flatpak)
Build and install:
```bash
flatpak-builder --user --install --force-clean build-dir com.milas.GlassDrop.yml
```

Run:
```bash
flatpak run com.milas.GlassDrop
```

## Installation (AppImage)
The repo contains a built AppImage at:
- `dist/GlassDrop-x86_64.AppImage`

Run:
```bash
chmod +x dist/GlassDrop-x86_64.AppImage
./dist/GlassDrop-x86_64.AppImage
```

AppImage runtime check:
```bash
./dist/GlassDrop-x86_64.AppImage --appimage-version
```

Rebuild AppImage (if needed):
```bash
ARCH=x86_64 /tmp/appimagetool.AppImage dist/GlassDrop.AppDir dist/GlassDrop-x86_64.AppImage
```

## Repository
- Homepage: https://github.com/Killersparrow1/GlassDrop
- Issues: https://github.com/Killersparrow1/GlassDrop/issues

## License
MIT
