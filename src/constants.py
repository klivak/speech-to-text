"""Константи та дефолтні значення додатку."""

from __future__ import annotations

APP_NAME = "VoiceType"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Voice-to-text input for Windows powered by OpenAI Whisper"

# Режими розпізнавання
MODE_LOCAL = "local"
MODE_API = "api"

# Мови
LANG_UK = "uk"
LANG_EN = "en"
SUPPORTED_LANGUAGES = {
    LANG_UK: "Українська",
    LANG_EN: "English",
}

# Моделі Whisper
WHISPER_MODELS = {
    "tiny": {"size_mb": 75, "description": "Найшвидша, низька точність"},
    "base": {"size_mb": 150, "description": "Швидка, прийнятна точність"},
    "small": {"size_mb": 500, "description": "Збалансована (рекомендовано)"},
    "medium": {"size_mb": 1500, "description": "Повільніша, висока точність"},
    "large-v3": {"size_mb": 3000, "description": "Найточніша, потребує GPU"},
}
DEFAULT_MODEL = "small"

# Пристрої
DEVICE_AUTO = "auto"
DEVICE_CPU = "cpu"
DEVICE_CUDA = "cuda"

# Гарячі клавіші
DEFAULT_HOTKEY = "ctrl+shift"
HOTKEY_MODE_PUSH = "push_to_talk"
HOTKEY_MODE_TOGGLE = "toggle"

# Оверлей
OVERLAY_SIZES = {"small": 80, "medium": 120, "large": 160}
OVERLAY_POSITIONS = {
    "center": "center",
    "top_center": "top_center",
    "bottom_center": "bottom_center",
}

# Плаваюча кнопка
FLOAT_BUTTON_SIZES = {"small": 36, "medium": 48, "large": 60}

# Звуки
SOUND_START = "start.wav"
SOUND_STOP = "stop.wav"
SOUND_SUCCESS = "success.wav"
SOUND_ERROR = "error.wav"

# Аудіо запис
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"

# Історія
MAX_HISTORY_ITEMS = 1000

# API
API_TIMEOUT = 30
API_MODEL = "whisper-1"

# Дефолтний конфіг
DEFAULT_CONFIG = {
    "version": APP_VERSION,
    "mode": MODE_LOCAL,
    "language": LANG_UK,
    "local": {
        "model": DEFAULT_MODEL,
        "device": DEVICE_AUTO,
        "fp16": False,
    },
    "api": {
        "api_key_configured": False,
        "model": API_MODEL,
        "timeout": API_TIMEOUT,
    },
    "hotkey": {
        "record": DEFAULT_HOTKEY,
        "mode": HOTKEY_MODE_PUSH,
        "switch_language": "",
        "switch_device": "",
    },
    "overlay": {
        "enabled": True,
        "size": "medium",
        "position": "center",
        "opacity": 0.8,
        "show_text": True,
    },
    "floating_button": {
        "enabled": False,
        "size": "medium",
        "position_x": -1,
        "position_y": -1,
    },
    "sounds": {
        "enabled": True,
        "volume": 0.5,
        "on_start": True,
        "on_stop": True,
        "on_success": True,
        "on_error": True,
    },
    "text_processing": {
        "voice_commands_enabled": True,
        "auto_capitalize": True,
        "auto_period": True,
    },
    "app": {
        "autostart": False,
        "minimize_to_tray": True,
        "check_updates": True,
        "theme": "system",
        "max_history": MAX_HISTORY_ITEMS,
    },
}

# Дефолтний словник технічних термінів
DEFAULT_DICTIONARY: dict[str, str] = {
    "flutter": "Flutter",
    "флаттер": "Flutter",
    "dart": "Dart",
    "дарт": "Dart",
    "javascript": "JavaScript",
    "джаваскрiпт": "JavaScript",
    "typescript": "TypeScript",
    "тайпскрiпт": "TypeScript",
    "react": "React",
    "реакт": "React",
    "vue": "Vue",
    "в'ю": "Vue",
    "вью": "Vue",
    "nuxt": "Nuxt",
    "накст": "Nuxt",
    "nodejs": "Node.js",
    "нод джей ес": "Node.js",
    "npm": "npm",
    "git": "Git",
    "гіт": "Git",
    "github": "GitHub",
    "гітхаб": "GitHub",
    "api": "API",
    "апі": "API",
    "json": "JSON",
    "html": "HTML",
    "css": "CSS",
    "http": "HTTP",
    "https": "HTTPS",
    "url": "URL",
    "docker": "Docker",
    "докер": "Docker",
    "kubernetes": "Kubernetes",
    "кубернетіс": "Kubernetes",
    "webpack": "Webpack",
    "вебпак": "Webpack",
    "vite": "Vite",
    "віт": "Vite",
    "tailwind": "Tailwind",
    "тейлвінд": "Tailwind",
    "laravel": "Laravel",
    "ларавел": "Laravel",
    "python": "Python",
    "пайтон": "Python",
    "widget": "Widget",
    "віджет": "Widget",
    "scaffold": "Scaffold",
    "скафолд": "Scaffold",
    "stateless": "Stateless",
    "stateful": "Stateful",
    "setState": "setState",
    "buildContext": "BuildContext",
    "pubspec": "pubspec",
    "async": "async",
    "await": "await",
    "const": "const",
    "final": "final",
    "override": "override",
    "null safety": "null safety",
    "hot reload": "hot reload",
    "хот рілоуд": "hot reload",
}

# Голосові команди пунктуації
DEFAULT_PUNCTUATION_COMMANDS: dict[str, str] = {
    # Українська
    "крапка": ".",
    "кома": ",",
    "знак питання": "?",
    "знак оклику": "!",
    "новий рядок": "\n",
    "новий абзац": "\n\n",
    "двокрапка": ":",
    "крапка з комою": ";",
    "тире": " \u2014 ",
    "дефіс": "-",
    "відкрити дужку": "(",
    "закрити дужку": ")",
    "лапки": '"',
    "три крапки": "...",
    # English
    "period": ".",
    "dot": ".",
    "comma": ",",
    "question mark": "?",
    "exclamation mark": "!",
    "new line": "\n",
    "new paragraph": "\n\n",
    "colon": ":",
    "semicolon": ";",
    "dash": " \u2014 ",
    "hyphen": "-",
    "open bracket": "(",
    "close bracket": ")",
    "quotes": '"',
    "ellipsis": "...",
}
