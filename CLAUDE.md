# CLAUDE.md -- VoiceType Project Guide

## Project Overview

VoiceType -- desktop Windows app for voice-to-text input powered by OpenAI Whisper.
Hold a hotkey, speak, release -- text is pasted into any active window.

## Tech Stack

- Python 3.9+
- PyQt6 -- GUI, system tray, overlay, settings window
- OpenAI Whisper -- local speech recognition
- OpenAI API -- cloud speech recognition (optional)
- sounddevice -- microphone recording
- keyboard -- global hotkeys
- keyring -- secure API key storage (Windows Credential Manager)

## Project Structure

```
src/
  main.py          -- entry point
  app.py           -- main coordinator (VoiceTypeApp), connects all components
  config.py        -- JSON config manager with dot-notation (config.get("local.model"))
  constants.py     -- all defaults, dictionaries, punctuation commands
  core/            -- business logic (recorder, transcribers, text processing, history)
  ui/              -- PyQt6 widgets (overlay, tray, settings, floating button)
  ui/themes/       -- dark.qss, light.qss, theme_manager.py
  audio/           -- sound notifications
  utils/           -- secure_key, clipboard, gpu_detect, log_filter, model_manager
tests/             -- pytest tests
assets/            -- icons, sounds, screenshots
```

## Commands

```bash
# Run app
python -m src.main

# Run tests
pytest tests/ -v --tb=short

# Lint
ruff check src/
ruff format --check src/

# Type check
mypy src/ --ignore-missing-imports

# Format
ruff check --fix src/
ruff format src/

# Build exe
pyinstaller --onefile --windowed --icon=assets/icon.ico --name=VoiceType --add-data "assets;assets" src/main.py
```

## Key Architecture Decisions

- **Threading**: Recording and transcription run in separate threads; communication via PyQt6 signals/slots
- **API key security**: NEVER store in config.json or logs. Only in env var, Windows Credential Manager, or .env file. Log filter auto-masks `sk-*` patterns.
- **CPU/GPU switching**: Model reloads in background thread without app restart
- **Config**: JSON file with dot-notation access. Merges missing keys from defaults on load.
- **Overlay**: Frameless transparent always-on-top QWidget with click-through. QPainter rendering at ~60 FPS.

## Conventions

- Code comments in Ukrainian
- Type hints on all functions
- Docstrings on all classes and public methods
- No emoji in code
- config.json, history.json, dictionary.json are in .gitignore (user data)
- API key is NEVER in config.json -- only `api_key_configured: true/false`
