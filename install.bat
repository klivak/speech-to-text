@echo off
echo ============================================
echo   VoiceType -- Installation
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found in PATH.
    echo Please install FFmpeg: https://ffmpeg.org/download.html
    echo Local Whisper mode requires FFmpeg.
    echo.
)

echo [3/3] Creating default config...
if not exist .env (
    copy .env.example .env >nul
    echo Created .env from .env.example
)

echo.
echo ============================================
echo   Installation complete!
echo   Run: python -m src.main
echo   Or:  run.bat
echo ============================================
pause
