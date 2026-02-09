@echo off
echo Starting VoiceType...
python -m src.main
if errorlevel 1 (
    echo.
    echo [ERROR] VoiceType exited with an error.
    pause
)
