@echo off
echo ============================================
echo   EchoScribe -- Build
echo ============================================
echo.

echo Installing PyInstaller...
pip install pyinstaller >nul 2>&1

echo Building EchoScribe.exe...
pyinstaller --onefile --windowed --icon=assets/icon.ico --name=EchoScribe ^
    --add-data "assets;assets" ^
    --add-data "src/ui/themes;src/ui/themes" ^
    --hidden-import "whisper" ^
    --hidden-import "sounddevice" ^
    --hidden-import "numpy" ^
    --hidden-import "keyring" ^
    --hidden-import "keyring.backends.Windows" ^
    src/main.py

if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build complete: dist\EchoScribe.exe
echo ============================================
pause
