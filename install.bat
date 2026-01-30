@echo off
title YT-DLP GUI - Complete Setup
color 0E

echo.
echo  ======================================================
echo       YT-DLP Premium GUI - Complete Setup
echo  ======================================================
echo.
echo  This script will install all required dependencies:
echo    - Python (via winget)
echo    - Deno (JavaScript Runtime)
echo    - FFmpeg (via winget)
echo    - yt-dlp with JS components
echo    - Required Python packages (requests, pillow)
echo.
echo  Press any key to start installation...
pause >nul

echo.
echo  [1/5] Checking/Installing Python...
echo  --------------------------------------------------------
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo  [!] Python may already be installed or winget failed.
    echo  [!] Please ensure Python 3.10+ is installed manually if needed.
)

echo.
echo  [2/5] Installing Deno (JavaScript Runtime)...
echo  --------------------------------------------------------
echo  [!] Deno is REQUIRED for YouTube downloads to work.
winget install DenoLand.Deno --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo  [!] Deno may already be installed or winget failed.
)

echo.
echo  [3/5] Installing FFmpeg (for video/audio merging)...
echo  --------------------------------------------------------
winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo  [!] FFmpeg may already be installed or winget failed.
    echo  [!] You can also download from: https://ffmpeg.org/download.html
)

echo.
echo  [4/5] Installing yt-dlp with JavaScript components...
echo  --------------------------------------------------------
pip install --upgrade "yt-dlp[default]"
if %errorlevel% neq 0 (
    echo  [!] Failed to install yt-dlp. Please run manually:
    echo      pip install "yt-dlp[default]"
)

echo.
echo  [5/5] Installing Python packages (requests, pillow)...
echo  --------------------------------------------------------
pip install --upgrade requests pillow
if %errorlevel% neq 0 (
    echo  [!] Failed to install packages. Please run manually:
    echo      pip install requests pillow
)

echo.
echo  ======================================================
echo       INSTALLATION COMPLETE!
echo  ======================================================
echo.
echo  You can now run the app with:
echo      python ytdlp.py
echo.
echo  If you encounter issues, try:
echo    1. Restart your terminal/command prompt
echo    2. Ensure Python, Deno, and FFmpeg are in your PATH
echo    3. Run 'deno --version' to verify Deno is installed
echo.
echo  Press any key to exit...
pause >nul
