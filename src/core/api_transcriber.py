"""Транскрайбер через OpenAI Whisper API."""

from __future__ import annotations

import io
import logging
import time
import wave

import numpy as np

from src.constants import API_MODEL, API_TIMEOUT, SAMPLE_RATE
from src.core.transcriber import BaseTranscriber, TranscriptionResult
from src.utils.secure_key import SecureKeyManager

logger = logging.getLogger(__name__)


class APITranscriber(BaseTranscriber):
    """Транскрайбер через OpenAI Whisper API (api.openai.com)."""

    def __init__(self, timeout: int = API_TIMEOUT) -> None:
        self._timeout = timeout
        self._model = API_MODEL

    def transcribe(self, audio: np.ndarray, language: str = "uk") -> TranscriptionResult:
        """Розпізнає мовлення через OpenAI API."""
        start_time = time.time()
        duration = len(audio) / SAMPLE_RATE

        api_key = SecureKeyManager.get_key()
        if not api_key:
            logger.error("API ключ не налаштовано.")
            return TranscriptionResult(
                text="",
                language=language,
                duration=duration,
                processing_time=0,
                mode="api",
                model=self._model,
            )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=self._timeout)

            # Конвертуємо numpy масив в WAV для API
            wav_buffer = self._audio_to_wav(audio)

            result = client.audio.transcriptions.create(
                model=self._model,
                file=("audio.wav", wav_buffer, "audio/wav"),
                language=language,
            )

            text = result.text.strip()
            processing_time = time.time() - start_time

            logger.info(
                "API розпізнано за %.1f сек: %s",
                processing_time,
                text[:80],
            )

            return TranscriptionResult(
                text=text,
                language=language,
                duration=duration,
                processing_time=processing_time,
                mode="api",
                model=self._model,
            )

        except Exception as e:
            logger.error("Помилка API розпізнавання: %s", e)
            return TranscriptionResult(
                text="",
                language=language,
                duration=duration,
                processing_time=time.time() - start_time,
                mode="api",
                model=self._model,
            )

    def is_available(self) -> bool:
        """Перевіряє доступність API."""
        return SecureKeyManager.is_configured()

    def get_info(self) -> dict[str, str]:
        """Інформація про транскрайбер."""
        return {
            "type": "api",
            "model": self._model,
            "configured": str(SecureKeyManager.is_configured()),
        }

    def test_connection(self) -> tuple[bool, str]:
        """Тестує з'єднання з API.

        Повертає (успіх, повідомлення).
        """
        api_key = SecureKeyManager.get_key()
        if not api_key:
            return False, "API ключ не налаштовано"

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=10)
            # Простий тестовий запит -- список моделей
            client.models.list()
            return True, "З'єднання успішне"
        except Exception as e:
            return False, f"Помилка: {e}"

    @staticmethod
    def _audio_to_wav(audio: np.ndarray) -> io.BytesIO:
        """Конвертує numpy масив в WAV формат для API."""
        buffer = io.BytesIO()

        # Конвертуємо float32 [-1.0, 1.0] в int16
        audio_int16 = (audio * 32767).astype(np.int16)

        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_int16.tobytes())

        buffer.seek(0)
        return buffer
