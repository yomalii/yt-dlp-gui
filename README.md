# YT-DLP Studio

Windows **yt-dlp GUI** for downloading YouTube (and other [yt-dlp](https://github.com/yt-dlp/yt-dlp)-supported sites). Pick format and quality, merge with **FFmpeg**, and use **Deno** for YouTube JavaScript challenges. Also branded **YT-DLP-GUI**. Portable build for **Windows 10/11**.

[![Windows](https://img.shields.io/badge/Windows-10%20%2F%2011-0078D6?logo=windows&logoColor=white)](https://github.com/yomalii/yt-dlp-gui)
[![Version](https://img.shields.io/badge/version-1.3.0-8b7cff)](https://github.com/yomalii/yt-dlp-gui)
[![yt-dlp](https://img.shields.io/badge/powered%20by-yt--dlp-red)](https://github.com/yt-dlp/yt-dlp)
[![Author](https://img.shields.io/badge/author-Shiraken12T-111111)](https://github.com/Shiraken12T)

## Features

- Paste a YouTube, TikTok, Instagram, or other yt-dlp URL, then **Analyze**
- Media types: video + audio, video only, audio only
- Formats: MP4, WebM, MP3, M4A
- Quality list from the video’s available streams (up to 8K when present)
- **Turbo**: 16 parallel download connections
- **Premiere**: force H.264 + AAC for video editors
- English SRT subtitles
- Recent URLs, save folder picker, save thumbnail
- Live size / speed / ETA
- Status bar for yt-dlp, FFmpeg, and Deno — **Fix deps** updates yt-dlp and rechecks them
- One automatic retry on connection timeout

## Requirements

- Windows 10 or 11
- Internet connection
- [FFmpeg](https://ffmpeg.org/) — merge video and audio
- [Deno](https://deno.land/) — YouTube JS challenges (HTTP 403 without it)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

Portable `setup.bat` needs [winget](https://learn.microsoft.com/windows/package-manager/winget/).  
Running or building from source also needs **Python 3** and `pip`.

## Quick start (portable)

1. Extract the ZIP to any folder
2. Run `setup.bat` once (installs FFmpeg, Deno, downloads official `yt-dlp.exe`)
3. Run `YT-DLP-GUI.exe`

The EXE is standalone and does **not** include Python. It needs `yt-dlp.exe` in the same folder. `setup.bat` downloads that binary from GitHub — it is required, not a duplicate.

If `setup.bat` fails:

```bat
winget install Gyan.FFmpeg
winget install DenoLand.Deno
```

Then download `yt-dlp.exe` from [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases) into the app folder.

## How to use

1. Paste or type a video URL
2. Click **Analyze**
3. Choose type, format, quality, and options
4. Click **Download**

## Troubleshooting

Click **Fix deps** at the top right of the window to reinstall or update dependencies (yt-dlp and a recheck of FFmpeg and Deno). Try that first if something is missing or a download fails.

**HTTP 403 / YouTube blocked**
- Click **Fix deps** at the top of the window
- Run `setup.bat` or `winget install DenoLand.Deno`
- Update yt-dlp: `pip install --upgrade "yt-dlp[default]"`

**No audio / merge failed**
- Install FFmpeg: `winget install Gyan.FFmpeg`
- Restart the app

**EXE cannot find yt-dlp**
- Click **Fix deps** at the top of the window
- Or run `setup.bat`, or put `yt-dlp.exe` next to `YT-DLP-GUI.exe`

**Connection timed out**
- Check your internet connection
- Try again (the app retries once)

## License

Use responsibly. Respect content creators and platform terms of service.

Made by [Shiraken12T](https://github.com/Shiraken12T). Downloads are handled by [yt-dlp](https://github.com/yt-dlp/yt-dlp).
