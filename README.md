<p align="center">
  <img src="app/assets/GlassDrop.png" alt="GlassDrop Logo" width="160" />
</p>

# GlassDrop

GlassDrop is a Linux GTK4/libadwaita video downloader and audio downloader powered by `yt-dlp`.
Paste a link, choose a format, and download.

## What it does
- Auto fetches title + thumbnail
- Lets you pick format/resolution or quick presets
- Shows download progress, queue, and history
- Works as Python app, Flatpak, or AppImage

## Screenshots
<details>
  <summary>Open screenshots (4)</summary>

  <p><strong>Python</strong></p>
  <img src="app/assets/screenshots/GlassDrop%20Python/GlassDrop%20Python.png" alt="GlassDrop Python Screenshot" />
  <img src="app/assets/screenshots/GlassDrop%20Python/GlassDrop%20Python%20FS.png" alt="GlassDrop Python Fullscreen Screenshot" />

  <p><strong>Flatpak</strong></p>
  <img src="app/assets/screenshots/GlassDrop%20Flatpak/GlassDrop%20Flatpak.png" alt="GlassDrop Flatpak Screenshot" />
  <img src="app/assets/screenshots/GlassDrop%20Flatpak/GlassDrop%20Flatpak%20FS.png" alt="GlassDrop Flatpak Fullscreen Screenshot" />
</details>

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

## Credits
- Built by Milas: `https://github.com/Killersparrow1`
- Download engine: `yt-dlp` (`https://github.com/yt-dlp/yt-dlp`)
- Development assistance: `Codex` (`https://github.com/openai/codex`)
- Cursor theme used in Flatpak package: `WhiteSur-cursors`

## License
MIT
