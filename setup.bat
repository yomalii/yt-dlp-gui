@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   YT-DLP Studio - First-Time Setup
echo ============================================
echo.

echo [1/3] Installing FFmpeg...
winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
if errorlevel 1 echo Warning: FFmpeg install may have failed. Install manually if needed.

echo.
echo [2/3] Installing Deno (YouTube JS runtime)...
winget install --id DenoLand.Deno -e --accept-source-agreements --accept-package-agreements
if errorlevel 1 echo Warning: Deno install may have failed. Install manually if needed.

echo.
echo [3/3] Downloading yt-dlp standalone...
echo.
echo   The GUI app (YT-DLP-GUI.exe) is a standalone program
echo   that cannot use Python. It needs yt-dlp.exe in this
echo   folder to download videos. This is NOT a duplicate -
echo   it is the official downloader the app calls directly.
echo.

powershell -NoProfile -Command ^
  "try { Invoke-WebRequest -Uri 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile '%~dp0yt-dlp.exe' -UseBasicParsing; Write-Host 'yt-dlp.exe downloaded successfully.' } catch { Write-Host 'Download failed:' $_.Exception.Message; exit 1 }"

if errorlevel 1 (
    echo.
    echo Failed to download yt-dlp.exe. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Setup complete!
echo   Run YT-DLP-GUI.exe to start.
echo ============================================
echo.
pause
endlocal
