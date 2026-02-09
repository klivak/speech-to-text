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


SOUND_PACKS = {
    "standard": "Стандартний",
    "minimal": "Мiнiмалiстичний",
    "scifi": "Sci-Fi",
}

DEFAULT_SOUND_PACK = "standard"


class SoundManager:
    """Менеджер звукових сповіщень додатку."""

    def __init__(
        self, enabled: bool = True, volume: float = 0.5, pack: str = DEFAULT_SOUND_PACK
    ) -> None:
        self._enabled = enabled
        self._volume = max(0.0, min(1.0, volume))
        self._base_dir = _get_assets_dir()
        self._pack = pack if pack in SOUND_PACKS else DEFAULT_SOUND_PACK
        self._sounds_dir = self._base_dir / self._pack
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

    @property
    def pack(self) -> str:
        return self._pack

    @pack.setter
    def pack(self, value: str) -> None:
        if value in SOUND_PACKS:
            self._pack = value
            self._sounds_dir = self._base_dir / self._pack

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

                winsound.PlaySound(  # type: ignore[attr-defined]
                    str(sound_file),
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,  # type: ignore[attr-defined]
                )
            else:
                logger.debug("Звуки підтримуються тільки на Windows.")
        except Exception as e:
            logger.debug("Помилка відтворення звуку: %s", e)


def _write_wav(filepath: str, samples: list[int], sample_rate: int = 44100) -> None:
    """Записує список семплiв у WAV файл."""
    with wave.open(filepath, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for s in samples:
            wav_file.writeframes(struct.pack("<h", max(-32768, min(32767, s))))


def _gen_standard(frequency: float, duration: float, volume: float) -> list[int]:
    """Стандартний набiр -- чистий тон з плавним згасанням."""
    import math

    sr = 44100
    n = int(sr * duration)
    out: list[int] = []
    for i in range(n):
        t = i / sr
        envelope = 1.0 - (i / n)
        val = volume * envelope * math.sin(2 * math.pi * frequency * t)
        out.append(int(val * 32767))
    return out


def _gen_minimal(frequency: float, duration: float, volume: float) -> list[int]:
    """Мiнiмалiстичний набiр -- м'який тон з швидким fade-in/out."""
    import math

    sr = 44100
    n = int(sr * duration)
    fade = int(sr * 0.02)
    out: list[int] = []
    for i in range(n):
        t = i / sr
        # Швидкий fade-in та fade-out
        if i < fade:
            env = i / fade
        elif i > n - fade:
            env = (n - i) / fade
        else:
            env = 1.0
        # М'який синус без обертонiв
        val = volume * 0.7 * env * math.sin(2 * math.pi * frequency * t)
        out.append(int(val * 32767))
    return out


def _gen_scifi(frequency: float, duration: float, volume: float) -> list[int]:
    """Sci-Fi набiр -- частотна модуляцiя та обертони."""
    import math

    sr = 44100
    n = int(sr * duration)
    out: list[int] = []
    for i in range(n):
        t = i / sr
        progress = i / n
        envelope = 1.0 - progress**0.5
        # Частотна модуляцiя -- свiп вгору
        sweep = frequency * (1.0 + progress * 0.5)
        # Основний тон + обертон
        val = (
            volume
            * envelope
            * (
                0.6 * math.sin(2 * math.pi * sweep * t)
                + 0.3 * math.sin(2 * math.pi * sweep * 2.0 * t)
                + 0.1 * math.sin(2 * math.pi * sweep * 3.0 * t)
            )
        )
        out.append(int(val * 32767))
    return out


# Конфiгурацiї звукiв для кожного набору
_PACK_CONFIGS: dict[str, dict[str, dict[str, float]]] = {
    "standard": {
        "start": {"frequency": 880.0, "duration": 0.1, "volume": 0.25},
        "stop": {"frequency": 660.0, "duration": 0.1, "volume": 0.25},
        "success": {"frequency": 1046.5, "duration": 0.15, "volume": 0.2},
        "error": {"frequency": 330.0, "duration": 0.25, "volume": 0.3},
    },
    "minimal": {
        "start": {"frequency": 600.0, "duration": 0.08, "volume": 0.2},
        "stop": {"frequency": 500.0, "duration": 0.08, "volume": 0.2},
        "success": {"frequency": 800.0, "duration": 0.12, "volume": 0.18},
        "error": {"frequency": 280.0, "duration": 0.15, "volume": 0.22},
    },
    "scifi": {
        "start": {"frequency": 1200.0, "duration": 0.15, "volume": 0.22},
        "stop": {"frequency": 800.0, "duration": 0.12, "volume": 0.22},
        "success": {"frequency": 1400.0, "duration": 0.2, "volume": 0.18},
        "error": {"frequency": 250.0, "duration": 0.3, "volume": 0.28},
    },
}

_GENERATORS = {
    "standard": _gen_standard,
    "minimal": _gen_minimal,
    "scifi": _gen_scifi,
}


def ensure_default_sounds() -> None:
    """Створює звуковi файли для всiх наборiв якщо вони вiдсутнi."""
    base = _get_assets_dir()

    for pack_name, configs in _PACK_CONFIGS.items():
        pack_dir = base / pack_name
        pack_dir.mkdir(parents=True, exist_ok=True)
        gen = _GENERATORS[pack_name]

        for sound_name, params in configs.items():
            filepath = pack_dir / f"{sound_name}.wav"
            if not filepath.exists():
                try:
                    samples = gen(params["frequency"], params["duration"], params["volume"])
                    _write_wav(str(filepath), samples)
                    logger.debug("Створено звук: %s/%s", pack_name, sound_name)
                except Exception as e:
                    logger.warning("Не вдалося створити звук %s/%s: %s", pack_name, sound_name, e)
