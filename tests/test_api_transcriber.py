"""Тести для APITranscriber."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.core.api_transcriber import APITranscriber


class TestAPITranscriber:
    """Тести API транскрайбера."""

    def test_is_available_without_key(self) -> None:
        """Недоступний без API ключа."""
        with patch("src.core.api_transcriber.SecureKeyManager") as mock_km:
            mock_km.is_configured.return_value = False
            at = APITranscriber()
            assert not at.is_available()

    def test_is_available_with_key(self) -> None:
        """Доступний з API ключем."""
        with patch("src.core.api_transcriber.SecureKeyManager") as mock_km:
            mock_km.is_configured.return_value = True
            at = APITranscriber()
            assert at.is_available()

    def test_get_info(self) -> None:
        """Інформація про транскрайбер."""
        with patch("src.core.api_transcriber.SecureKeyManager") as mock_km:
            mock_km.is_configured.return_value = True
            at = APITranscriber()
            info = at.get_info()
            assert info["type"] == "api"
            assert info["model"] == "whisper-1"

    def test_transcribe_without_key(self) -> None:
        """Розпізнавання без ключа повертає порожній результат."""
        with patch("src.core.api_transcriber.SecureKeyManager") as mock_km:
            mock_km.get_key.return_value = None
            at = APITranscriber()
            audio = np.zeros(16000, dtype=np.float32)
            result = at.transcribe(audio, "uk")
            assert result.is_empty
            assert result.mode == "api"

    def test_audio_to_wav_conversion(self) -> None:
        """Конвертація numpy масиву в WAV."""
        audio = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        wav_buffer = APITranscriber._audio_to_wav(audio)

        assert isinstance(wav_buffer, io.BytesIO)
        # WAV файл починається з RIFF заголовка
        wav_buffer.seek(0)
        header = wav_buffer.read(4)
        assert header == b"RIFF"

    def test_test_connection_without_key(self) -> None:
        """Тест з'єднання без ключа."""
        with patch("src.core.api_transcriber.SecureKeyManager") as mock_km:
            mock_km.get_key.return_value = None
            at = APITranscriber()
            success, message = at.test_connection()
            assert not success
            assert "не налаштовано" in message
