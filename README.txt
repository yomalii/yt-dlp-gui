YT-DLP Studio v1.3.0 - Portable Edition
======================================

QUICK START
-----------
1. Extract the ZIP to any folder
2. Run setup.bat once (installs FFmpeg, Deno, downloads yt-dlp.exe)
3. Run YT-DLP-GUI.exe

REQUIREMENTS
------------
- Windows 10/11
- Internet connection
- setup.bat needs winget (Windows Package Manager)

WHY DOES setup.bat CREATE yt-dlp.exe?
--------------------------------------
The GUI app (YT-DLP-GUI.exe) is a standalone program — it does
NOT include Python. To download videos it needs yt-dlp.exe in
the same folder. setup.bat downloads the official standalone
binary from GitHub. This is required and is not a duplicate bug.

FIRST-TIME SETUP (setup.bat)
----------------------------
setup.bat will:
  - Install FFmpeg (video/audio merging)
  - Install Deno (YouTube JavaScript challenges)
  - Download official yt-dlp.exe from GitHub into this folder

If setup.bat fails, install manually:
  winget install Gyan.FFmpeg
  winget install DenoLand.Deno
  Download yt-dlp.exe from: https://github.com/yt-dlp/yt-dlp/releases

USING THE APP
-------------
1. Paste or type a video URL
2. Click SEARCH to fetch metadata
3. Choose type, format, quality, and options
4. Click START DOWNLOAD

FEATURES
--------
- Turbo Mode: 16 parallel download connections
- Premiere Compat: Forces H.264 + AAC for video editors
- Subtitles: Download English SRT subtitles
- Recent URLs: Quick access to past searches
- Dependency status: Shows yt-dlp, FFmpeg, Deno status at top

TROUBLESHOOTING
---------------
HTTP 403 / YouTube blocked:
  - Run setup.bat or: winget install DenoLand.Deno
  - Click FIX DEPS in the app
  - Update yt-dlp: pip install --upgrade "yt-dlp[default]"

No audio / merge failed:
  - Install FFmpeg: winget install Gyan.FFmpeg
  - Restart the app after installing

EXE cannot find yt-dlp:
  - Run setup.bat to copy yt-dlp.exe to the app folder
  - Or place yt-dlp.exe in the same folder as YT-DLP-GUI.exe

Connection timed out:
  - Check your internet connection
  - Try again (app auto-retries once)

BUILD FROM SOURCE
-----------------
  pip install -r requirements.txt
  build.bat
  package.bat

Output: dist\YT-DLP-GUI-portable.zip

LICENSE
-------
Use responsibly. Respect content creators and platform terms of service.
