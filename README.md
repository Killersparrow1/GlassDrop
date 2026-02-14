<p align="center">
  <img src="app/assets/GlassDrop.png" alt="GlassDrop Logo" width="160" />
</p>

# GlassDrop

GlassDrop is a small GTK app for downloading videos/audio with `yt-dlp`.
Paste a link, choose a format, and download.

## What it does
- Auto fetches title + thumbnail
- Lets you pick format/resolution or quick presets
- Shows download progress, queue, and history
- Works as Python app, Flatpak, or AppImage

## Quick start (Python)
Requirements:
- Linux
- Python `3.10+`
- `yt-dlp`
- `PyGObject` / GTK 4 runtime

Run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app/main.py
```

## Flatpak
Build and install:
```bash
flatpak-builder --user --install --force-clean build-dir com.milas.GlassDrop.yml
```

Run:
```bash
flatpak run com.milas.GlassDrop
```

## AppImage
Run the prebuilt file:
```bash
chmod +x dist/GlassDrop-x86_64.AppImage
./dist/GlassDrop-x86_64.AppImage
```

## Download
Release files:
- AppImage: `GlassDrop-x86_64.AppImage`
- Flatpak bundle: `GlassDrop.flatpak`

From Releases:
`https://github.com/Killersparrow1/GlassDrop/releases`

## License
MIT
