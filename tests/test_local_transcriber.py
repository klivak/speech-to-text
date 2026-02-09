"""Тести для LocalTranscriber."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.core.local_transcriber import LocalTranscriber


class TestLocalTranscriber:
    """Тести локального транскрайбера."""

    def test_initial_state(self) -> None:
        """Початковий стан транскрайбера."""
        with patch("src.core.local_transcriber.get_optimal_device", return_value="cpu"):
            lt = LocalTranscriber.__new__(LocalTranscriber)
            lt._model_name = "small"
            lt._model = None
            lt._current_device = None
            lt._fp16 = False
            lt._loading = False
            lt._load_error = None

            assert lt.model_name == "small"
            assert lt.current_device is None
            assert not lt.is_loading

    @patch("src.core.local_transcriber.get_optimal_device", return_value="cpu")
    def test_is_available_without_whisper(self, mock_device: MagicMock) -> None:
        """Перевірка доступності без встановленого whisper."""
        lt = LocalTranscriber.__new__(LocalTranscriber)
        lt._model_name = "small"
        lt._model = None
        lt._current_device = None
        lt._fp16 = False
        lt._loading = False
        lt._load_error = None

        with patch.dict("sys.modules", {"whisper": None}):
            # Якщо whisper не встановлено -- ImportError
            with patch("builtins.__import__", side_effect=ImportError):
                assert not lt.is_available()

    def test_get_info(self) -> None:
        """Отримання інформації про транскрайбер."""
        lt = LocalTranscriber.__new__(LocalTranscriber)
        lt._model_name = "small"
        lt._model = None
        lt._current_device = "cpu"
        lt._fp16 = False
        lt._loading = False
        lt._load_error = None

        info = lt.get_info()
        assert info["type"] == "local"
        assert info["model"] == "small"
        assert info["device"] == "cpu"

    def test_transcribe_without_model(self) -> None:
        """Розпізнавання без завантаженої моделі повертає порожній результат."""
        import threading

        lt = LocalTranscriber.__new__(LocalTranscriber)
        lt._model_name = "small"
        lt._model = None
        lt._current_device = "cpu"
        lt._fp16 = False
        lt._loading = False
        lt._load_error = None
        lt._lock = threading.Lock()

        audio = np.zeros(16000, dtype=np.float32)  # 1 секунда тиші
        result = lt.transcribe(audio, "uk")
        assert result.is_empty
        assert result.mode == "local"

    def test_transcribe_with_mock_model(self) -> None:
        """Розпізнавання з мок-моделлю."""
        import threading

        lt = LocalTranscriber.__new__(LocalTranscriber)
        lt._model_name = "small"
        lt._current_device = "cpu"
        lt._fp16 = False
        lt._loading = False
        lt._load_error = None
        lt._lock = threading.Lock()

        # Мок модель
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "тестовий текст"}
        lt._model = mock_model

        audio = np.zeros(16000, dtype=np.float32)
        result = lt.transcribe(audio, "uk")

        assert result.text == "тестовий текст"
        assert result.mode == "local"
        assert result.model == "small"
        assert result.language == "uk"
        mock_model.transcribe.assert_called_once()
