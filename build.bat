@echo off
setlocal
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    exit /b 1
)

echo Building YT-DLP-GUI.exe...
python -m PyInstaller ytdlp.spec --noconfirm
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo.
echo Build complete: dist\YT-DLP-GUI.exe
echo Run package.bat to create the portable ZIP.
endlocal
