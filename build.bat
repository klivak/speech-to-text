@echo off
echo ============================================
echo   VoiceType -- Build
echo ============================================
echo.

echo Installing PyInstaller...
pip install pyinstaller >nul 2>&1

echo Building VoiceType.exe...
pyinstaller --onefile --windowed --icon=assets/icon.ico --name=VoiceType ^
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
echo   Build complete: dist\VoiceType.exe
echo ============================================
pause
