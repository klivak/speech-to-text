# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-02-09

### Added
- Voice input with push-to-talk and toggle hotkey modes
- Local Whisper transcription (offline) with model selection (tiny/base/small/medium/large-v3)
- OpenAI Whisper API transcription mode (online)
- Visual overlay with 4 states: recording (amplitude visualization), processing, success, error
- Click-through transparent overlay rendered via QPainter at ~60 FPS
- System tray icon with context menu (language, device, settings, history, quit)
- Full settings GUI with 9 tabs (General, API, Model, Hotkeys, Overlay, Sounds, Text, Dictionary, Statistics)
- Floating draggable microphone button (disabled by default)
- Recognition history with search, export to TXT, per-entry copy/delete
- Statistics: daily counts, total audio duration, average speed, most used language
- Custom technical dictionary with 50+ default entries for dev terms (Flutter, React, Python, etc.)
- Dictionary import/export (JSON), search, reset to defaults
- Voice punctuation commands in Ukrainian and English (period, comma, question mark, new line, etc.)
- Dark and Light QSS themes with automatic Windows system theme detection
- CPU/GPU (CUDA) switching without app restart, background model reloading
- Secure API key storage via Windows Credential Manager (keyring), env var, or .env file
- API key never stored in config.json or logs; automatic sk-* pattern masking in all log output
- Sound notifications for start, stop, success, error (auto-generated WAV tones)
- Auto-capitalization after sentences and auto-period at end of text
- Text pasting via clipboard with original clipboard content preservation
- Graceful shutdown with position saving for floating button
- `__main__.py` for `python -m src` execution
- 82 unit tests covering config, text processing, dictionary, history, transcribers, recorder, security, log filter
- CI/CD: GitHub Actions for lint/test (Python 3.9-3.12, Windows), release (.exe build), security scanning
- Pre-commit hooks: ruff lint/format, detect-secrets, detect-private-key
- GitHub issue templates (bug report, feature request), PR template, CODEOWNERS
- Full documentation: README.md (EN), README.uk.md (UK), CONTRIBUTING.md, SECURITY.md, CLAUDE.md
- Install/run/build batch scripts and Makefile
- PyInstaller build support for single-file .exe distribution

### Security
- API keys stored only in Windows Credential Manager or environment variables
- SecretFilter logging handler masks all sk-* patterns automatically
- TruffleHog CI scanning for leaked secrets
- .env in .gitignore, config.json stores only `api_key_configured: bool`

### Technical
- Python 3.9+ compatibility with `from __future__ import annotations`
- PyQt6 for all GUI with QueuedConnection for cross-thread signal safety
- Thread-safe hotkey manager with lock-protected state
- Efficient queue replacement instead of loop-clearing in audio recorder
- Proper type hints on all PyQt6 event handlers
