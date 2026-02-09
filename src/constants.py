"""Константи та дефолтні значення додатку."""

from __future__ import annotations

APP_NAME = "EchoScribe"
APP_VERSION = "1.4.0"
APP_DESCRIPTION = "Voice-to-text input for Windows powered by OpenAI Whisper"

# Режими розпізнавання
MODE_LOCAL = "local"
MODE_API = "api"

# Мови
LANG_UK = "uk"
LANG_EN = "en"
LANG_AUTO = "auto"
SUPPORTED_LANGUAGES = {
    LANG_AUTO: "Автовизначення",
    LANG_UK: "Українська",
    LANG_EN: "English",
}

# Моделі Whisper
WHISPER_MODELS = {
    "tiny": {"size_mb": 75, "ram_mb": 400, "description": "Найшвидша, низька точність"},
    "base": {"size_mb": 150, "ram_mb": 600, "description": "Швидка, прийнятна точність"},
    "small": {"size_mb": 500, "ram_mb": 1500, "description": "Збалансована (рекомендовано)"},
    "medium": {"size_mb": 1500, "ram_mb": 4000, "description": "Повільніша, висока точність"},
    "large-v3": {"size_mb": 3000, "ram_mb": 9000, "description": "Найточніша, потребує GPU"},
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
    "mode": MODE_API,
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
        "pack": "standard",
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
        "copy_to_clipboard": True,
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
    # Мовні виправлення
    "чі": "чи",
    "щі": "щи",
    # Фреймворки та мови програмування
    "flutter": "Flutter",
    "флаттер": "Flutter",
    "dart": "Dart",
    "дарт": "Dart",
    "javascript": "JavaScript",
    "джаваскрiпт": "JavaScript",
    "джаваскріпт": "JavaScript",
    "typescript": "TypeScript",
    "тайпскрiпт": "TypeScript",
    "тайпскріпт": "TypeScript",
    "react": "React",
    "реакт": "React",
    "react native": "React Native",
    "реакт нейтів": "React Native",
    "angular": "Angular",
    "ангуляр": "Angular",
    "vue": "Vue",
    "в'ю": "Vue",
    "вью": "Vue",
    "nuxt": "Nuxt",
    "накст": "Nuxt",
    "next": "Next.js",
    "некст": "Next.js",
    "svelte": "Svelte",
    "свелт": "Svelte",
    "nodejs": "Node.js",
    "нод джей ес": "Node.js",
    "нода": "Node.js",
    "express": "Express",
    "експрес": "Express",
    "nestjs": "NestJS",
    "fastapi": "FastAPI",
    "django": "Django",
    "джанго": "Django",
    "flask": "Flask",
    "фласк": "Flask",
    "spring": "Spring",
    "спрінг": "Spring",
    "ruby on rails": "Ruby on Rails",
    "рубі он рейлс": "Ruby on Rails",
    "python": "Python",
    "пайтон": "Python",
    "java": "Java",
    "джава": "Java",
    "kotlin": "Kotlin",
    "котлін": "Kotlin",
    "swift": "Swift",
    "свіфт": "Swift",
    "rust": "Rust",
    "раст": "Rust",
    "golang": "Go",
    "csharp": "C#",
    "сі шарп": "C#",
    "php": "PHP",
    "пхп": "PHP",
    "ruby": "Ruby",
    "рубі": "Ruby",
    "lua": "Lua",
    "scala": "Scala",
    "elixir": "Elixir",
    # Інструменти та платформи
    "npm": "npm",
    "yarn": "yarn",
    "pnpm": "pnpm",
    "pip": "pip",
    "conda": "conda",
    "git": "Git",
    "гіт": "Git",
    "github": "GitHub",
    "гітхаб": "GitHub",
    "gitlab": "GitLab",
    "гітлаб": "GitLab",
    "bitbucket": "Bitbucket",
    "docker": "Docker",
    "докер": "Docker",
    "kubernetes": "Kubernetes",
    "кубернетіс": "Kubernetes",
    "кубер": "Kubernetes",
    "terraform": "Terraform",
    "терраформ": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "дженкінс": "Jenkins",
    "webpack": "Webpack",
    "вебпак": "Webpack",
    "vite": "Vite",
    "віт": "Vite",
    "rollup": "Rollup",
    "esbuild": "esbuild",
    "babel": "Babel",
    "eslint": "ESLint",
    "prettier": "Prettier",
    "tailwind": "Tailwind",
    "тейлвінд": "Tailwind",
    "bootstrap": "Bootstrap",
    "бутстрап": "Bootstrap",
    "figma": "Figma",
    "фігма": "Figma",
    "postman": "Postman",
    "jira": "Jira",
    "джіра": "Jira",
    "confluence": "Confluence",
    "slack": "Slack",
    "notion": "Notion",
    "vercel": "Vercel",
    "netlify": "Netlify",
    "heroku": "Heroku",
    "aws": "AWS",
    "azure": "Azure",
    "firebase": "Firebase",
    "файрбейс": "Firebase",
    "supabase": "Supabase",
    "redis": "Redis",
    "редіс": "Redis",
    "mongodb": "MongoDB",
    "монго": "MongoDB",
    "postgres": "PostgreSQL",
    "постгрес": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "elasticsearch": "Elasticsearch",
    "graphql": "GraphQL",
    "граф кю ел": "GraphQL",
    # Концепції та терміни
    "api": "API",
    "апі": "API",
    "rest api": "REST API",
    "рест апі": "REST API",
    "sdk": "SDK",
    "cli": "CLI",
    "gui": "GUI",
    "ide": "IDE",
    "json": "JSON",
    "xml": "XML",
    "yaml": "YAML",
    "html": "HTML",
    "css": "CSS",
    "sass": "SASS",
    "scss": "SCSS",
    "sql": "SQL",
    "http": "HTTP",
    "https": "HTTPS",
    "url": "URL",
    "uri": "URI",
    "dns": "DNS",
    "ssh": "SSH",
    "ssl": "SSL",
    "tls": "TLS",
    "tcp": "TCP",
    "udp": "UDP",
    "cors": "CORS",
    "jwt": "JWT",
    "oauth": "OAuth",
    "ci cd": "CI/CD",
    "devops": "DevOps",
    "девопс": "DevOps",
    "agile": "Agile",
    "scrum": "Scrum",
    "скрам": "Scrum",
    "kanban": "Kanban",
    "crud": "CRUD",
    "orm": "ORM",
    "mvc": "MVC",
    "mvvm": "MVVM",
    "solid": "SOLID",
    "dry": "DRY",
    "kiss": "KISS",
    "tdd": "TDD",
    "bdd": "BDD",
    "regex": "regex",
    "regexp": "regexp",
    # Flutter / Dart
    "widget": "Widget",
    "віджет": "Widget",
    "scaffold": "Scaffold",
    "скафолд": "Scaffold",
    "stateless": "Stateless",
    "stateful": "Stateful",
    "setState": "setState",
    "buildContext": "BuildContext",
    "pubspec": "pubspec",
    "riverpod": "Riverpod",
    "bloc": "BLoC",
    "getx": "GetX",
    "provider": "Provider",
    # Загальні програмістські
    "async": "async",
    "await": "await",
    "const": "const",
    "final": "final",
    "override": "override",
    "null safety": "null safety",
    "hot reload": "hot reload",
    "хот рілоуд": "hot reload",
    "frontend": "frontend",
    "фронтенд": "frontend",
    "backend": "backend",
    "бекенд": "backend",
    "fullstack": "fullstack",
    "фулстек": "fullstack",
    "localhost": "localhost",
    "deploy": "deploy",
    "деплой": "deploy",
    "merge": "merge",
    "мердж": "merge",
    "commit": "commit",
    "коміт": "commit",
    "pull request": "pull request",
    "пул реквест": "pull request",
    "code review": "code review",
    "код рев'ю": "code review",
    "refactor": "refactor",
    "рефактор": "refactor",
    "debug": "debug",
    "дебаг": "debug",
    "баг": "bug",
    "фіча": "feature",
    "фікс": "fix",
    "хотфікс": "hotfix",
    "бранч": "branch",
    "репозиторій": "repository",
    "репо": "repo",
    "ендпоінт": "endpoint",
    "мідлвер": "middleware",
    "вебсокет": "WebSocket",
    "вебхук": "webhook",
    "тайпінг": "typing",
    "лінтер": "linter",
    "компілятор": "compiler",
    "рантайм": "runtime",
    "фреймворк": "framework",
    "лібрарі": "library",
    "бібліотека": "library",
    "пакет": "package",
    "модуль": "module",
    "компонент": "component",
    "інтерфейс": "interface",
    "абстракція": "abstraction",
    "інстанс": "instance",
    "об'єкт": "object",
    "масив": "array",
    "стрінг": "string",
    "булеан": "boolean",
    "нулл": "null",
    "андефайнд": "undefined",
    "колбек": "callback",
    "проміс": "promise",
    "ітератор": "iterator",
    "генератор": "generator",
    "декоратор": "decorator",
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
