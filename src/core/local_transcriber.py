"""Локальний транскрайбер на основі OpenAI Whisper з підтримкою перемикання CPU/GPU."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import numpy as np

from src.constants import DEFAULT_MODEL, SAMPLE_RATE
from src.core.transcriber import BaseTranscriber, TranscriptionResult
from src.utils.gpu_detect import get_optimal_device

logger = logging.getLogger(__name__)


class LocalTranscriber(BaseTranscriber):
    """Локальний транскрайбер Whisper з перемиканням пристрою в реальному часі."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "auto",
        fp16: bool = False,
    ) -> None:
        self._model_name = model_name
        self._model: Any = None
        self._current_device: str | None = None
        self._fp16 = fp16
        self._lock = threading.Lock()
        self._loading = False
        self._load_error: str | None = None

        # Ініціалізуємо модель
        self.set_device(device)

    @property
    def model_name(self) -> str:
        """Назва поточної моделі."""
        return self._model_name

    @property
    def current_device(self) -> str | None:
        """Поточний пристрій обчислення."""
        return self._current_device

    @property
    def is_loading(self) -> bool:
        """Чи завантажується модель зараз."""
        return self._loading

    def set_device(self, device: str) -> None:
        """Перемикає пристрій обчислення.

        Модель перезавантажується у фоновому потоці.
        device: "auto", "cpu", "cuda"
        """
        if device == "auto":
            device = get_optimal_device()

        if device == self._current_device and self._model is not None:
            return

        self._load_error = None

        def _reload() -> None:
            self._loading = True
            try:
                import whisper

                logger.info(
                    "Завантаження моделі %s на %s...",
                    self._model_name,
                    device,
                )
                with self._lock:
                    self._model = whisper.load_model(self._model_name, device=device)
                    self._current_device = device
                logger.info(
                    "Модель %s готова на %s.",
                    self._model_name,
                    device,
                )
            except Exception as e:
                self._load_error = str(e)
                logger.error("Помилка завантаження моделі: %s", e)
            finally:
                self._loading = False

        thread = threading.Thread(target=_reload, daemon=True)
        thread.start()

    def set_model(self, model_name: str) -> None:
        """Змінює модель Whisper."""
        if model_name == self._model_name and self._model is not None:
            return
        self._model_name = model_name
        self._model = None
        self.set_device(self._current_device or "auto")

    def transcribe(self, audio: np.ndarray, language: str = "uk") -> TranscriptionResult:
        """Розпізнає мовлення через локальний Whisper.

        Якщо language="auto", Whisper автоматично визначає мову.
        """
        start_time = time.time()
        duration = len(audio) / SAMPLE_RATE
        # language=None для Whisper означає auto-detect
        whisper_lang = None if language == "auto" else language

        with self._lock:
            if self._model is None:
                return TranscriptionResult(
                    text="",
                    language=language,
                    duration=duration,
                    processing_time=0,
                    mode="local",
                    model=self._model_name,
                    device=self._current_device or "unknown",
                )

            try:
                # Whisper очікує float32 numpy масив
                audio_float: np.ndarray = audio.astype(np.float32)

                result = self._model.transcribe(
                    audio_float,
                    language=whisper_lang,
                    fp16=self._fp16 and self._current_device == "cuda",
                    task="transcribe",
                )

                text = result.get("text", "").strip()
                detected_lang = result.get("language", language)
                processing_time = time.time() - start_time

                logger.info(
                    "Розпізнано за %.1f сек (%s, %s, мова: %s): %s",
                    processing_time,
                    self._model_name,
                    self._current_device,
                    detected_lang,
                    text[:80],
                )

                return TranscriptionResult(
                    text=text,
                    language=detected_lang,
                    duration=duration,
                    processing_time=processing_time,
                    mode="local",
                    model=self._model_name,
                    device=self._current_device or "unknown",
                )

            except Exception as e:
                logger.error("Помилка розпізнавання: %s", e)
                return TranscriptionResult(
                    text="",
                    language=language,
                    duration=duration,
                    processing_time=time.time() - start_time,
                    mode="local",
                    model=self._model_name,
                    device=self._current_device or "unknown",
                )

    def is_available(self) -> bool:
        """Перевіряє доступність локального Whisper."""
        try:
            import whisper  # noqa: F401

            return True
        except ImportError:
            return False

    def get_info(self) -> dict[str, str]:
        """Інформація про транскрайбер."""
        return {
            "type": "local",
            "model": self._model_name,
            "device": self._current_device or "not loaded",
            "fp16": str(self._fp16),
            "status": "loading" if self._loading else ("ready" if self._model else "not loaded"),
        }

    def wait_for_model(self, timeout: float = 60.0) -> bool:
        """Чекає завантаження моделі.

        Повертає True якщо модель завантажена успішно.
        """
        start = time.time()
        while self._loading and (time.time() - start) < timeout:
            time.sleep(0.1)
        return self._model is not None

    def benchmark(self, duration_sec: float = 5.0) -> dict[str, float | str]:
        """Запускає бенчмарк: транскрибує тестове аудіо і повертає результати.

        Повертає dict з ключами: device, model, audio_duration, processing_time,
        realtime_factor (скільки секунд аудіо на 1 секунду обробки).
        """
        with self._lock:
            if self._model is None:
                return {"error": "Модель не завантажена"}

            # Генеруємо тестове аудіо (тиша з невеликим шумом)
            samples = int(SAMPLE_RATE * duration_sec)
            test_audio = np.random.randn(samples).astype(np.float32) * 0.01

            start_time = time.time()
            try:
                self._model.transcribe(
                    test_audio,
                    language="uk",
                    fp16=self._fp16 and self._current_device == "cuda",
                    task="transcribe",
                )
            except Exception as e:
                return {"error": str(e)}
            processing_time = time.time() - start_time

            realtime_factor = duration_sec / processing_time if processing_time > 0 else 0

            logger.info(
                "Benchmark: %.1f сек аудіо за %.1f сек (%s, %s). RTF: %.2fx",
                duration_sec,
                processing_time,
                self._model_name,
                self._current_device,
                realtime_factor,
            )

            return {
                "device": self._current_device or "unknown",
                "model": self._model_name,
                "audio_duration": duration_sec,
                "processing_time": round(processing_time, 2),
                "realtime_factor": round(realtime_factor, 2),
            }
