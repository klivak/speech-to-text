"""Запис аудіо з мікрофона через sounddevice."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal

from src.constants import CHANNELS, DTYPE, SAMPLE_RATE

logger = logging.getLogger(__name__)


class AudioRecorder(QObject):
    """Запис аудіо з мікрофона.

    Сигнали:
        amplitude_changed: float -- поточна RMS амплітуда (0.0 - 1.0)
        recording_finished: numpy.ndarray -- записане аудіо
        error_occurred: str -- повідомлення про помилку
    """

    amplitude_changed = pyqtSignal(float)
    recording_finished = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS) -> None:
        super().__init__()
        self._sample_rate = sample_rate
        self._channels = channels
        self._is_recording = False
        self._audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        """Чи йде запис зараз."""
        return self._is_recording

    @property
    def sample_rate(self) -> int:
        """Частота дискретизації."""
        return self._sample_rate

    def start(self) -> None:
        """Починає запис з мікрофона."""
        with self._lock:
            if self._is_recording:
                logger.warning("Запис вже йде.")
                return

            # Створюємо нову чергу замість очищення старої
            self._audio_queue = queue.Queue()

            try:
                self._stream = sd.InputStream(
                    samplerate=self._sample_rate,
                    channels=self._channels,
                    dtype=DTYPE,
                    callback=self._audio_callback,
                    blocksize=1024,
                )
                self._stream.start()
                self._is_recording = True
                logger.info("Запис розпочато.")
            except Exception as e:
                error_msg = f"Помилка запуску запису: {e}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)

    def stop(self) -> None:
        """Зупиняє запис та повертає аудіо через сигнал recording_finished."""
        with self._lock:
            if not self._is_recording:
                return

            self._is_recording = False

            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.warning("Помилка зупинки потоку: %s", e)
                self._stream = None

        # Збираємо всі записані фрейми
        frames: list[np.ndarray] = []
        while not self._audio_queue.empty():
            try:
                frames.append(self._audio_queue.get_nowait())
            except queue.Empty:
                break

        if frames:
            audio_data = np.concatenate(frames, axis=0).flatten()
            duration = len(audio_data) / self._sample_rate
            logger.info("Запис завершено. Тривалість: %.1f сек.", duration)
            self.recording_finished.emit(audio_data)
        else:
            logger.warning("Запис порожній.")
            self.error_occurred.emit("Запис порожній -- не вдалося захопити аудіо.")

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback для sounddevice InputStream."""
        if status:
            logger.warning("Статус аудіо потоку: %s", status)

        if self._is_recording:
            self._audio_queue.put(indata.copy())

            # Обчислюємо RMS амплітуду для візуалізації
            rms = float(np.sqrt(np.mean(indata**2)))
            # Нормалізуємо до діапазону 0.0-1.0 (типова мова ~0.01-0.1)
            normalized = min(rms * 10.0, 1.0)
            self.amplitude_changed.emit(normalized)

    @staticmethod
    def get_input_devices() -> list[dict[str, object]]:
        """Повертає список доступних вхідних аудіопристроїв."""
        devices = sd.query_devices()
        input_devices: list[dict[str, object]] = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                input_devices.append(
                    {
                        "id": i,
                        "name": dev["name"],
                        "channels": dev["max_input_channels"],
                        "sample_rate": dev["default_samplerate"],
                    }
                )
        return input_devices
