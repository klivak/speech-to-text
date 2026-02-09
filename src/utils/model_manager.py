"""Менеджер моделей Whisper -- завантаження, кешування, статус."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from src.constants import WHISPER_MODELS

logger = logging.getLogger(__name__)


def get_cache_dir() -> Path:
    """Повертає директорію кешу моделей Whisper."""
    custom = os.environ.get("WHISPER_CACHE_DIR")
    if custom:
        return Path(custom)
    return Path.home() / ".cache" / "whisper"


def get_model_path(model_name: str) -> Path:
    """Повертає очікуваний шлях до файлу моделі."""
    return get_cache_dir() / f"{model_name}.pt"


def is_model_downloaded(model_name: str) -> bool:
    """Перевіряє чи модель вже завантажена."""
    # Whisper зберігає моделі як .pt файли в кеш-директорії
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        return False

    # Перевіряємо наявність будь-якого файлу з назвою моделі
    return any(model_name in f.name and f.suffix == ".pt" for f in cache_dir.iterdir())


def get_model_size_mb(model_name: str) -> int:
    """Повертає очікуваний розмір моделі в мегабайтах."""
    info = WHISPER_MODELS.get(model_name, {})
    return int(info.get("size_mb", 0))  # type: ignore[call-overload,no-any-return]


def get_models_status() -> dict[str, dict[str, object]]:
    """Повертає статус всіх доступних моделей."""
    result: dict[str, dict[str, object]] = {}
    for name, info in WHISPER_MODELS.items():
        result[name] = {
            "size_mb": info["size_mb"],
            "description": info["description"],
            "downloaded": is_model_downloaded(name),
        }
    return result


def download_model(model_name: str) -> bool:
    """Завантажує модель Whisper.

    Повертає True якщо завантаження успішне.
    Whisper автоматично завантажує модель при першому використанні,
    але ця функція дозволяє зробити це явно.
    """
    if model_name not in WHISPER_MODELS:
        logger.error("Невідома модель: %s", model_name)
        return False

    try:
        import whisper

        logger.info("Завантаження моделі %s...", model_name)
        whisper.load_model(model_name, device="cpu")
        logger.info("Модель %s завантажено успішно.", model_name)
        return True
    except Exception as e:
        logger.error("Помилка завантаження моделі %s: %s", model_name, e)
        return False
