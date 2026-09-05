@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\YT-DLP-GUI.exe" (
    echo dist\YT-DLP-GUI.exe not found. Run build.bat first.
    exit /b 1
)

set OUT=dist\YT-DLP-GUI-Portable
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"

copy /Y "dist\YT-DLP-GUI.exe" "%OUT%\"
copy /Y "setup.bat" "%OUT%\"
copy /Y "README.txt" "%OUT%\"

if exist "yt-dlp.exe" copy /Y "yt-dlp.exe" "%OUT%\"

echo Creating ZIP...
powershell -NoProfile -Command "Compress-Archive -Path '%OUT%\*' -DestinationPath 'dist\YT-DLP-GUI-portable.zip' -Force"

echo.
echo Portable package ready:
echo   Folder: %OUT%
echo   ZIP:    dist\YT-DLP-GUI-portable.zip
endlocal
