# streamrip 🎬

A lightweight desktop tool for downloading HLS and DASH video streams with a clean GUI. Built with Python and tkinter no browser extension, no bloat.

---

## Features

- **HLS (.m3u8)** —> downloads muxed streams (video + audio in one) at best quality
- **Real-time progress** —> live percentage, download speed, and ETA
- **Episode naming** —> set show name, season, and episode number; generates filenames like `Naruto_S01E04.mp4`
- **Manual episode increment** —> ＋ button to step to the next episode between downloads
- **Parallel fragment downloading** —> 16 concurrent fragments via yt-dlp for maximum speed
- **Completion sound** —> three-tone beep when download finishes
- **Episode list** —> shows recently downloaded files in the save folder
- **No console window** —> clean GUI-only experience on Windows

---

## Requirements

### Python
- Python 3.8 or higher —> https://www.python.org/downloads/

### Dependencies

Install with pip:

```bash
pip install yt-dlp
```

### FFmpeg

Required for merging and fixing streams.

1. Download from https://www.gyan.dev/ffmpeg/builds/ → `ffmpeg-release-essentials.zip`
2. Extract to `C:\ffmpeg-8.1.1-essentials_build\` (or any folder)
3. Add `C:\ffmpeg-8.1.1-essentials_build\bin` to your system PATH in Environment variables

Verify:
```bash
ffmpeg -version
```

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/streamrip.git
cd streamrip
pip install yt-dlp
```

---

## Usage

```bash
python streamrip.py
```

### Steps

1. **Paste the master m3u8 URL** — get it from your browser's DevTools (F12 → Network → filter `m3u8` → play video → copy the master playlist URL)
2. **Set show name, season, episode** — e.g. `Naruto`, `1`, `4` → saves as `Naruto_S01E04.mp4`
3. **Choose save folder** — defaults to `~/Videos`
4. **Click Download**

### Getting the m3u8 URL

1. Open the streaming site in Chrome or Firefox
2. Press `F12` → go to the **Network** tab
3. Press play on the video
4. Filter by `m3u8`
5. Look for the **master playlist** — usually named `master.m3u8` or similar, hosted on a CDN domain
6. Right-click → Copy URL
7. Paste into streamrip

> ⚠️ Tokens in m3u8 URLs expire — grab a fresh URL each session.

---

## File Structure

```
streamrip/
├── streamrip.py   # Main GUI application (HLS muxed streams)
├──    # HLS downloader with separate audio tracks (FR/EN)
├── README.md
```

---

## Configuration

FFmpeg path is hardcoded at the top of each script:

```python
FFMPEG = r"C:\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"
```

Change this to match your FFmpeg installation path if different.

---

## Tested On

| Platform | Python | Status |
|----------|--------|--------|
| Windows 11 | 3.14 | ✅ Working |
| Windows 10 | 3.10+ | ✅ Working |

---

## Known Limitations

- **DRM-protected streams** (Widevine, PlayReady) are not supported and cannot be supported — this includes Crunchyroll, Netflix, Disney+, etc.
- **Tokens expire** — m3u8 URLs are time-limited; if download fails immediately, get a fresh URL
- macOS/Linux support is untested (FFmpeg path and `winsound` are Windows-specific)

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `yt-dlp` | HLS/DASH stream downloading, fragment management |
| `ffmpeg` | Stream fixing, muxing, merging audio+video |
| `tkinter` | GUI (built into Python) |
| `winsound` | Completion sound (built into Python on Windows) |

---

## Disclaimer

This repository is provided as-is for educational purposes only. The authors do not condone software piracy.
