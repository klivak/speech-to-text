"""Тести для ConfigManager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import ConfigManager
from src.constants import DEFAULT_CONFIG


class TestConfigManager:
    """Тести менеджера конфігурації."""

    def test_creates_default_config(self, config_path: str) -> None:
        """Створює дефолтну конфігурацію якщо файл не існує."""
        config = ConfigManager(config_path)
        assert Path(config_path).exists()
        assert config.get("mode") == "local"
        assert config.get("language") == "uk"

    def test_loads_existing_config(self, config_path: str) -> None:
        """Завантажує існуючу конфігурацію."""
        data = {"mode": "api", "language": "en", "version": "1.0.0"}
        with open(config_path, "w") as f:
            json.dump(data, f)

        config = ConfigManager(config_path)
        assert config.get("mode") == "api"
        assert config.get("language") == "en"

    def test_dot_notation_get(self, config_path: str) -> None:
        """Отримання значення через крапкову нотацію."""
        config = ConfigManager(config_path)
        assert config.get("local.model") == "small"
        assert config.get("local.device") == "auto"
        assert config.get("hotkey.record") == "ctrl+shift"

    def test_dot_notation_set(self, config_path: str) -> None:
        """Встановлення значення через крапкову нотацію."""
        config = ConfigManager(config_path)
        config.set("local.model", "medium")
        assert config.get("local.model") == "medium"

        # Перезавантажуємо та перевіряємо збереження
        config2 = ConfigManager(config_path)
        assert config2.get("local.model") == "medium"

    def test_get_default_value(self, config_path: str) -> None:
        """Повертає дефолтне значення для неіснуючого ключа."""
        config = ConfigManager(config_path)
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "fallback") == "fallback"

    def test_get_section(self, config_path: str) -> None:
        """Отримання цілої секції."""
        config = ConfigManager(config_path)
        local = config.get_section("local")
        assert isinstance(local, dict)
        assert "model" in local
        assert "device" in local

    def test_set_section(self, config_path: str) -> None:
        """Встановлення цілої секції."""
        config = ConfigManager(config_path)
        config.set_section("local", {"model": "large-v3", "device": "cuda", "fp16": True})
        assert config.get("local.model") == "large-v3"
        assert config.get("local.fp16") is True

    def test_reset(self, config_path: str) -> None:
        """Скидання до дефолтних значень."""
        config = ConfigManager(config_path)
        config.set("mode", "api")
        config.set("language", "en")

        config.reset()
        assert config.get("mode") == "local"
        assert config.get("language") == "uk"

    def test_merges_missing_defaults(self, config_path: str) -> None:
        """Доповнює конфігурацію відсутніми дефолтними значеннями."""
        # Мінімальний конфіг
        with open(config_path, "w") as f:
            json.dump({"mode": "api"}, f)

        config = ConfigManager(config_path)
        # Має бути доповнений дефолтними
        assert config.get("language") == "uk"
        assert config.get("local.model") == "small"
        # Але збережене значення -- те що було
        assert config.get("mode") == "api"

    def test_handles_corrupt_config(self, config_path: str) -> None:
        """Обробляє пошкоджений конфіг файл."""
        with open(config_path, "w") as f:
            f.write("{invalid json")

        config = ConfigManager(config_path)
        # Має використати дефолтні
        assert config.get("mode") == "local"
