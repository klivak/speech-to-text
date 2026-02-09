"""Менеджер конфігурації -- читання та запис налаштувань в JSON."""

from __future__ import annotations

import copy
import json
import logging
import os
from pathlib import Path
from typing import Any

from src.constants import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ConfigManager:
    """Менеджер конфігурації додатку.

    Зберігає налаштування в JSON файлі. API ключі зберігаються
    окремо через SecureKeyManager, НЕ в config.json.
    """

    def __init__(self, config_path: str | None = None) -> None:
        if config_path is None:
            config_path = os.environ.get("CONFIG_PATH", "config.json")
        self._path = Path(config_path)
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Завантажує конфігурацію з файлу або створює дефолтну."""
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    self._data = json.load(f)
                # Доповнюємо відсутні ключі дефолтними значеннями
                self._data = self._merge_defaults(DEFAULT_CONFIG, self._data)
                logger.info("Конфігурацію завантажено з %s", self._path)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Помилка читання конфігурації: %s. Використовуємо дефолтну.", e)
                self._data = copy.deepcopy(DEFAULT_CONFIG)
                self._save()
        else:
            logger.info("Файл конфігурації не знайдено, створюємо дефолтний.")
            self._data = copy.deepcopy(DEFAULT_CONFIG)
            self._save()

    def _merge_defaults(self, defaults: dict, current: dict) -> dict:
        """Рекурсивно доповнює поточну конфігурацію відсутніми дефолтними значеннями."""
        result = copy.deepcopy(current)
        for key, value in defaults.items():
            if key not in result:
                result[key] = copy.deepcopy(value)
            elif isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._merge_defaults(value, result[key])
        return result

    def _save(self) -> None:
        """Зберігає конфігурацію в файл."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug("Конфігурацію збережено в %s", self._path)
        except OSError as e:
            logger.error("Помилка збереження конфігурації: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """Отримує значення за ключем з підтримкою крапкової нотації.

        Приклад: config.get("local.model") -> "small"
        """
        keys = key.split(".")
        value: Any = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Встановлює значення за ключем з підтримкою крапкової нотації та зберігає."""
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
        self._save()

    def get_section(self, section: str) -> dict[str, Any]:
        """Повертає цілу секцію конфігурації."""
        return copy.deepcopy(self._data.get(section, {}))

    def set_section(self, section: str, data: dict[str, Any]) -> None:
        """Встановлює цілу секцію конфігурації та зберігає."""
        self._data[section] = data
        self._save()

    def reset(self) -> None:
        """Скидає конфігурацію до дефолтних значень."""
        self._data = copy.deepcopy(DEFAULT_CONFIG)
        self._save()
        logger.info("Конфігурацію скинуто до дефолтних значень.")

    @property
    def data(self) -> dict[str, Any]:
        """Повна копія конфігурації."""
        return copy.deepcopy(self._data)

    @property
    def path(self) -> Path:
        """Шлях до файлу конфігурації."""
        return self._path
