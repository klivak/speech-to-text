"""Транскрайбер через хмарнi API (OpenAI, Groq, Deepgram)."""

from __future__ import annotations

import io
import logging
import time
import wave

import numpy as np

from src.constants import (
    API_PROVIDER_DEEPGRAM,
    API_PROVIDER_OPENAI,
    API_PROVIDERS,
    API_TIMEOUT,
    SAMPLE_RATE,
)
from src.core.transcriber import BaseTranscriber, TranscriptionResult
from src.utils.secure_key import SecureKeyManager

logger = logging.getLogger(__name__)


class APITranscriber(BaseTranscriber):
    """Транскрайбер через хмарнi API.

    Пiдтримує провайдерiв:
    - OpenAI (whisper-1)
    - Groq (whisper-large-v3-turbo, OpenAI-сумiсний)
    - Deepgram (nova-2, власний REST API)
    """

    def __init__(
        self,
        provider: str = API_PROVIDER_OPENAI,
        timeout: int = API_TIMEOUT,
    ) -> None:
        self._provider = provider
        self._timeout = timeout
        provider_info = API_PROVIDERS.get(provider, API_PROVIDERS[API_PROVIDER_OPENAI])
        self._model: str = str(provider_info["model"])
        self._base_url: str | None = provider_info.get("base_url")  # type: ignore[assignment]

    @property
    def provider(self) -> str:
        """Поточний провайдер."""
        return self._provider

    @provider.setter
    def provider(self, value: str) -> None:
        """Змiнює провайдера."""
        self._provider = value
        provider_info = API_PROVIDERS.get(value, API_PROVIDERS[API_PROVIDER_OPENAI])
        self._model = str(provider_info["model"])
        self._base_url = provider_info.get("base_url")  # type: ignore[assignment]

    def transcribe(self, audio: np.ndarray, language: str = "uk") -> TranscriptionResult:
        """Розпізнає мовлення через обраний API."""
        if self._provider == API_PROVIDER_DEEPGRAM:
            return self._transcribe_deepgram(audio, language)
        return self._transcribe_openai_compatible(audio, language)

    def _transcribe_openai_compatible(
        self, audio: np.ndarray, language: str
    ) -> TranscriptionResult:
        """Розпiзнавання через OpenAI-сумiсний API (OpenAI, Groq)."""
        start_time = time.time()
        duration = len(audio) / SAMPLE_RATE

        api_key = SecureKeyManager.get_key(self._provider)
        if not api_key:
            logger.error("API ключ (%s) не налаштовано.", self._provider)
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

            client_kwargs: dict = {"api_key": api_key, "timeout": self._timeout}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            client = OpenAI(**client_kwargs)

            wav_buffer = self._audio_to_wav(audio)

            api_kwargs: dict = {
                "model": self._model,
                "file": ("audio.wav", wav_buffer, "audio/wav"),
            }
            if language != "auto":
                api_kwargs["language"] = language

            result = client.audio.transcriptions.create(**api_kwargs)

            text = result.text.strip()
            processing_time = time.time() - start_time

            logger.info(
                "API (%s) розпізнано за %.1f сек: %s",
                self._provider,
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
            logger.error("Помилка API (%s) розпізнавання: %s", self._provider, e)
            return TranscriptionResult(
                text="",
                language=language,
                duration=duration,
                processing_time=time.time() - start_time,
                mode="api",
                model=self._model,
            )

    def _transcribe_deepgram(self, audio: np.ndarray, language: str) -> TranscriptionResult:
        """Розпiзнавання через Deepgram REST API."""
        start_time = time.time()
        duration = len(audio) / SAMPLE_RATE

        api_key = SecureKeyManager.get_key(API_PROVIDER_DEEPGRAM)
        if not api_key:
            logger.error("API ключ (deepgram) не налаштовано.")
            return TranscriptionResult(
                text="",
                language=language,
                duration=duration,
                processing_time=0,
                mode="api",
                model=self._model,
            )

        try:
            import httpx

            wav_buffer = self._audio_to_wav(audio)

            params: dict[str, str] = {"model": self._model, "smart_format": "true"}
            if language != "auto":
                params["language"] = language

            response = httpx.post(
                "https://api.deepgram.com/v1/listen",
                params=params,
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "audio/wav",
                },
                content=wav_buffer.read(),
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()

            text = ""
            channels = data.get("results", {}).get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                if alternatives:
                    text = alternatives[0].get("transcript", "").strip()

            processing_time = time.time() - start_time

            logger.info(
                "API (deepgram) розпізнано за %.1f сек: %s",
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
            logger.error("Помилка API (deepgram) розпізнавання: %s", e)
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
        return SecureKeyManager.is_configured(self._provider)

    def get_info(self) -> dict[str, str]:
        """Інформація про транскрайбер."""
        return {
            "type": "api",
            "provider": self._provider,
            "model": self._model,
            "configured": str(SecureKeyManager.is_configured(self._provider)),
        }

    def test_connection(self) -> tuple[bool, str]:
        """Тестує з'єднання з API.

        Повертає (успіх, повідомлення).
        """
        api_key = SecureKeyManager.get_key(self._provider)
        if not api_key:
            return False, "API ключ не налаштовано"

        if self._provider == API_PROVIDER_DEEPGRAM:
            return self._test_deepgram(api_key)
        return self._test_openai_compatible(api_key)

    def _test_openai_compatible(self, api_key: str) -> tuple[bool, str]:
        """Тест зʼєднання для OpenAI-сумiсних API."""
        try:
            from openai import OpenAI

            client_kwargs: dict = {"api_key": api_key, "timeout": 10}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            client = OpenAI(**client_kwargs)
            client.models.list()
            return True, "З'єднання успішне"
        except Exception as e:
            return False, f"Помилка: {e}"

    def _test_deepgram(self, api_key: str) -> tuple[bool, str]:
        """Тест зʼєднання для Deepgram API."""
        try:
            import httpx

            response = httpx.get(
                "https://api.deepgram.com/v1/projects",
                headers={"Authorization": f"Token {api_key}"},
                timeout=10,
            )
            response.raise_for_status()
            return True, "З'єднання успішне"
        except Exception as e:
            return False, f"Помилка: {e}"

    @staticmethod
    def _audio_to_wav(audio: np.ndarray) -> io.BytesIO:
        """Конвертує numpy масив в WAV формат для API."""
        buffer = io.BytesIO()

        # Конвертуємо float32 [-1.0, 1.0] в int16
        audio_int16: np.ndarray = (audio * 32767).astype(np.int16)

        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_int16.tobytes())

        buffer.seek(0)
        return buffer
