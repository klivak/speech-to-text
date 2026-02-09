"""Менеджер звукових сповіщень."""

from __future__ import annotations

import logging
import os
import struct
import sys
import wave
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_assets_dir() -> Path:
    """Повертає шлях до директорії assets."""
    if getattr(sys, "frozen", False):
        # PyInstaller bundle
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).parent.parent.parent
    return base / "assets" / "sounds"


class SoundManager:
    """Менеджер звукових сповіщень додатку."""

    def __init__(self, enabled: bool = True, volume: float = 0.5) -> None:
        self._enabled = enabled
        self._volume = max(0.0, min(1.0, volume))
        self._sounds_dir = _get_assets_dir()
        self._sound_enabled = {
            "start": True,
            "stop": True,
            "success": True,
            "error": True,
        }

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))

    def set_sound_enabled(self, sound_name: str, enabled: bool) -> None:
        """Вмикає/вимикає окремий звук."""
        if sound_name in self._sound_enabled:
            self._sound_enabled[sound_name] = enabled

    def play_start(self) -> None:
        """Звук початку запису."""
        self._play("start")

    def play_stop(self) -> None:
        """Звук кінця запису."""
        self._play("stop")

    def play_success(self) -> None:
        """Звук успішного розпізнавання."""
        self._play("success")

    def play_error(self) -> None:
        """Звук помилки."""
        self._play("error")

    def _play(self, sound_name: str) -> None:
        """Відтворює звук якщо він увімкнений."""
        if not self._enabled:
            return
        if not self._sound_enabled.get(sound_name, True):
            return

        sound_file = self._sounds_dir / f"{sound_name}.wav"
        if not sound_file.exists():
            logger.debug("Звуковий файл не знайдено: %s", sound_file)
            return

        try:
            # Використовуємо winsound на Windows
            if os.name == "nt":
                import winsound

                winsound.PlaySound(
                    str(sound_file),
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
            else:
                logger.debug("Звуки підтримуються тільки на Windows.")
        except Exception as e:
            logger.debug("Помилка відтворення звуку: %s", e)


def generate_tone_wav(
    filepath: str,
    frequency: float = 440.0,
    duration: float = 0.15,
    sample_rate: int = 44100,
    volume: float = 0.3,
) -> None:
    """Генерує простий тон та зберігає як WAV файл.

    Використовується для створення дефолтних звуків при першому запуску.
    """
    import math

    num_samples = int(sample_rate * duration)
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        # Огинаюча для плавного згасання
        envelope = 1.0 - (i / num_samples)
        sample = volume * envelope * math.sin(2 * math.pi * frequency * t)
        samples.append(int(sample * 32767))

    with wave.open(filepath, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample in samples:
            wav_file.writeframes(struct.pack("<h", max(-32768, min(32767, sample))))


def ensure_default_sounds() -> None:
    """Створює дефолтні звукові файли якщо вони відсутні."""
    sounds_dir = _get_assets_dir()
    sounds_dir.mkdir(parents=True, exist_ok=True)

    sound_configs = {
        "start.wav": {"frequency": 880.0, "duration": 0.1, "volume": 0.25},
        "stop.wav": {"frequency": 660.0, "duration": 0.1, "volume": 0.25},
        "success.wav": {"frequency": 1046.5, "duration": 0.15, "volume": 0.2},
        "error.wav": {"frequency": 330.0, "duration": 0.25, "volume": 0.3},
    }

    for filename, config in sound_configs.items():
        filepath = sounds_dir / filename
        if not filepath.exists():
            try:
                generate_tone_wav(str(filepath), **config)  # type: ignore[arg-type]
                logger.debug("Створено звуковий файл: %s", filename)
            except Exception as e:
                logger.warning("Не вдалося створити звук %s: %s", filename, e)
