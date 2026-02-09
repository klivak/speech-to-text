"""Базовий клас транскрайбера (абстрактний інтерфейс)."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class TranscriptionResult:
    """Результат розпізнавання мовлення."""

    text: str
    language: str
    duration: float = 0.0
    processing_time: float = 0.0
    mode: str = ""
    model: str = ""
    device: str = ""
    timestamp: float = field(default_factory=time.time)

    @property
    def is_empty(self) -> bool:
        """Чи порожній результат."""
        return not self.text.strip()


class BaseTranscriber(ABC):
    """Абстрактний базовий клас для транскрайберів."""

    @abstractmethod
    def transcribe(self, audio: np.ndarray, language: str = "uk") -> TranscriptionResult:
        """Розпізнає мовлення з аудіо масиву.

        Args:
            audio: NumPy масив з аудіо даними (float32, 16kHz, mono).
            language: Код мови для розпізнавання ("uk" або "en").

        Returns:
            TranscriptionResult з розпізнаним текстом.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Перевіряє чи транскрайбер доступний для використання."""
        ...

    @abstractmethod
    def get_info(self) -> dict[str, str]:
        """Повертає інформацію про транскрайбер."""
        ...
