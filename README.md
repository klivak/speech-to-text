# EchoScribe

**Voice-to-text input for Windows powered by OpenAI Whisper**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Windows 10/11](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)]()
[![CI](https://github.com/klivak/speech-to-text/actions/workflows/ci.yml/badge.svg)](https://github.com/klivak/speech-to-text/actions)

> Hold a hotkey, speak, release -- text is instantly pasted into any application.

<!-- ![Demo](assets/screenshots/demo.gif) -->

## Features

- **Two recognition modes**: Local (offline, Whisper on your PC) and API (OpenAI cloud)
- **Push-to-talk**: Hold hotkey to record, release to transcribe and paste
- **Visual overlay**: Pulsating circle with amplitude visualization while recording
- **System tray**: Quick access to settings, language and device switching
- **Floating mic button**: Optional draggable button as hotkey alternative
- **Custom dictionary**: Map spoken words to correct technical terms
- **Voice punctuation**: Say "period", "comma", "new line" etc.
- **CPU/GPU switching**: Switch between CPU and NVIDIA GPU without restart
- **Dark/Light theme**: Follows Windows system theme or manual override
- **Recognition history**: Search, export, and statistics
- **Secure API key**: Stored in Windows Credential Manager, never in files
- **Ukrainian + English**: Two languages with quick switching

## Recognition Speed

Time from releasing the hotkey to text insertion (for a ~5 second phrase):

### Local Mode (Whisper)

| Model | Size | CPU (i5/i7) | NVIDIA GPU | Accuracy |
|-------|------|-------------|------------|----------|
| `tiny` | 75 MB | 1-3 sec | <1 sec | Low |
| `base` | 150 MB | 2-5 sec | ~1 sec | Acceptable |
| `small` | 500 MB | 3-7 sec | 1-2 sec | Good (recommended) |
| `medium` | 1.5 GB | 8-20 sec | 2-5 sec | Very good |
| `large-v3` | 3 GB | 15-40 sec | 3-8 sec | Best |

### API Mode (OpenAI)

| Parameter | Value |
|-----------|-------|
| Speed | 1-2 seconds regardless of PC |
| Accuracy | Best |
| Cost | ~$0.006/minute |
| Internet required | Yes |
| API key required | Yes |

### Recommendations
- Have NVIDIA GPU -- Local mode, `small` or `medium` model
- No GPU, powerful CPU -- Local mode, `small` model
- Weak PC -- API mode
- No internet -- Local mode only

## Quick Start

### Local Mode (default, no API key needed)

```bash
# Clone
git clone https://github.com/klivak/speech-to-text.git
cd speech-to-text

# Install dependencies
pip install -r requirements.txt

# Run
python -m src.main
```

### API Mode

```bash
# Install
pip install -r requirements.txt

# Set API key (option 1: environment variable)
set OPENAI_API_KEY=sk-your-key-here

# Or create .env file (option 2)
copy .env.example .env
# Edit .env and add your key

# Run
python -m src.main
# Then switch to API mode in Settings
```

### GPU Support (NVIDIA)

```bash
# Install with CUDA support
pip install -r requirements-gpu.txt
```

## Installation

### Prerequisites
- **Python 3.9+** -- [python.org](https://www.python.org/downloads/)
- **FFmpeg** -- Required for local Whisper mode
  - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - Add to system PATH
- **NVIDIA GPU** (optional) -- For faster local transcription

### Using install script
```bash
install.bat
```

### Manual
```bash
pip install -r requirements.txt       # Base
pip install -r requirements-gpu.txt   # With GPU support
pip install -r requirements-dev.txt   # For development
```

## Usage

### Hotkeys
| Action | Default | Configurable |
|--------|---------|-------------|
| Record (push-to-talk) | `Ctrl+Shift` (hold) | Yes |
| Switch language | Not set | Yes |
| Switch CPU/GPU | Not set | Yes |

### Voice Punctuation Commands

| Command (UK) | Command (EN) | Result |
|-------------|-------------|--------|
| "крапка" | "period" / "dot" | `.` |
| "кома" | "comma" | `,` |
| "знак питання" | "question mark" | `?` |
| "знак оклику" | "exclamation mark" | `!` |
| "новий рядок" | "new line" | `\n` |
| "новий абзац" | "new paragraph" | `\n\n` |
| "двокрапка" | "colon" | `:` |
| "тире" | "dash" | ` -- ` |
| "лапки" | "quotes" | `"` |
| "три крапки" | "ellipsis" | `...` |

### Custom Dictionary

Add technical terms that Whisper might misrecognize:

| Spoken | Written |
|--------|---------|
| "флаттер" | Flutter |
| "пайтон" | Python |
| "реакт" | React |
| "гітхаб" | GitHub |

Edit in Settings > Dictionary tab or in `dictionary.json`.

## Configuration

Settings are stored in `config.json` (auto-generated). Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| Mode | Local | `local` or `api` |
| Language | Ukrainian | `uk` or `en` |
| Model | small | Whisper model name |
| Device | auto | `auto`, `cpu`, `cuda` |
| Theme | system | `system`, `light`, `dark` |
| Hotkey | ctrl+shift | Any key combination |
| Overlay | enabled | Visual recording indicator |

**API key is stored separately** in Windows Credential Manager, never in config files.

**Whisper models cache**: `%USERPROFILE%\.cache\whisper\` (e.g. `C:\Users\<user>\.cache\whisper\`). You can safely delete unused model files (`.pt`) from this directory to free disk space.

## Security

- API keys are stored in **Windows Credential Manager** (OS-level encryption)
- Keys are **never** written to config.json, logs, or source code
- Log output automatically masks any `sk-*` patterns
- Pre-commit hooks detect accidental secret commits
- CI includes TruffleHog secret scanning

See [SECURITY.md](SECURITY.md) for the full security policy.

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt
pre-commit install

# Run tests
pytest tests/ -v

# Lint
ruff check src/
ruff format --check src/

# Type check
mypy src/ --ignore-missing-imports

# Build exe
pyinstaller --onefile --windowed --icon=assets/icon.ico --name=EchoScribe --add-data "assets;assets" src/main.py
```

## Roadmap

### Features
- [ ] Continuous recording with automatic pause detection
- [ ] Multilingual mode -- auto-detect language
- [ ] Voice macros -- "insert signature" pastes predefined text
- [ ] Transcription mode -- record lectures/meetings to text file
- [ ] Real-time translation -- dictate in UK, paste in EN
- [ ] Context dictionaries -- auto-switch dictionary based on active app
- [ ] Voice control -- "undo", "delete last word", "select all"
- [ ] Faster Whisper integration for 2-4x speed boost
- [ ] Streaming -- text appears in real-time while speaking
- [ ] Text templates -- "client letter" inserts template with fields

### Interface
- [ ] Text animation in overlay before pasting
- [ ] Mini-panel with last recognized text and edit button
- [ ] Overlay themes (different pulse animation styles)
- [ ] Multi-monitor support

### Technical
- [ ] Single-file .exe via PyInstaller
- [ ] NSIS/Inno Setup installer
- [ ] Auto-update from GitHub Releases
- [ ] Whisper.cpp backend for maximum speed
- [ ] WebSocket server for external integrations
- [ ] Settings profiles (work, personal, coding)
- [ ] Portable mode (all data in one folder)

### Integrations
- [ ] VS Code extension
- [ ] Obsidian plugin for voice notes
- [ ] CLI: `echoscribe --file audio.mp3 --output text.txt`
- [ ] Telegram bot -- voice message to text
- [ ] REST API server for local network

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) -- speech recognition model
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) -- GUI framework
- [sounddevice](https://python-sounddevice.readthedocs.io/) -- audio recording
