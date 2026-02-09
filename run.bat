@echo off
echo Starting EchoScribe...
python -m src.main
if errorlevel 1 (
    echo.
    echo [ERROR] EchoScribe exited with an error.
    pause
)
