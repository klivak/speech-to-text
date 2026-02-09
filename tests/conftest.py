"""Pytest fixtures для VoiceType."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.constants import DEFAULT_CONFIG, DEFAULT_DICTIONARY


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Тимчасова директорія для тестів."""
    return tmp_path


@pytest.fixture
def config_path(temp_dir: Path) -> str:
    """Шлях до тимчасового config.json."""
    return str(temp_dir / "config.json")


@pytest.fixture
def history_path(temp_dir: Path) -> str:
    """Шлях до тимчасового history.json."""
    return str(temp_dir / "history.json")


@pytest.fixture
def dictionary_path(temp_dir: Path) -> str:
    """Шлях до тимчасового dictionary.json."""
    return str(temp_dir / "dictionary.json")


@pytest.fixture
def sample_config(config_path: str) -> str:
    """Створює тимчасовий config.json з дефолтними значеннями."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f)
    return config_path


@pytest.fixture
def sample_dictionary(dictionary_path: str) -> str:
    """Створює тимчасовий dictionary.json."""
    with open(dictionary_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_DICTIONARY, f)
    return dictionary_path
