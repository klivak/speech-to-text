"""Постобробка розпізнаного тексту -- пунктуація, капіталізація, голосові команди."""

from __future__ import annotations

import logging
import re

from src.constants import DEFAULT_PUNCTUATION_COMMANDS

logger = logging.getLogger(__name__)


class TextProcessor:
    """Обробка тексту після розпізнавання.

    Застосовує голосові команди пунктуації, авто-капіталізацію,
    та заміни зі словника.
    """

    def __init__(
        self,
        punctuation_commands: dict[str, str] | None = None,
        auto_capitalize: bool = True,
        auto_period: bool = True,
        voice_commands_enabled: bool = True,
    ) -> None:
        self._punctuation = punctuation_commands or dict(DEFAULT_PUNCTUATION_COMMANDS)
        self._auto_capitalize = auto_capitalize
        self._auto_period = auto_period
        self._voice_commands_enabled = voice_commands_enabled

    @property
    def punctuation_commands(self) -> dict[str, str]:
        """Поточні команди пунктуації."""
        return dict(self._punctuation)

    def update_settings(
        self,
        auto_capitalize: bool | None = None,
        auto_period: bool | None = None,
        voice_commands_enabled: bool | None = None,
    ) -> None:
        """Оновлює налаштування обробки."""
        if auto_capitalize is not None:
            self._auto_capitalize = auto_capitalize
        if auto_period is not None:
            self._auto_period = auto_period
        if voice_commands_enabled is not None:
            self._voice_commands_enabled = voice_commands_enabled

    def set_punctuation_commands(self, commands: dict[str, str]) -> None:
        """Встановлює нові команди пунктуації."""
        self._punctuation = dict(commands)

    def process(self, text: str, dictionary: dict[str, str] | None = None) -> str:
        """Застосовує всю постобробку до тексту.

        Args:
            text: Розпізнаний текст.
            dictionary: Словник замін (spoken -> written).

        Returns:
            Оброблений текст.
        """
        if not text:
            return text

        result = text.strip()

        # 1. Голосові команди пунктуації
        if self._voice_commands_enabled:
            result = self._apply_punctuation_commands(result)

        # 2. Словник технічних термінів
        if dictionary:
            result = self._apply_dictionary(result, dictionary)

        # 3. Авто-капіталізація
        if self._auto_capitalize:
            result = self._capitalize(result)

        # 4. Авто-крапка
        if self._auto_period:
            result = self._add_period(result)

        return result

    def _apply_punctuation_commands(self, text: str) -> str:
        """Замінює голосові команди пунктуації на символи."""
        result = text

        # Сортуємо за довжиною (довші спочатку) щоб уникнути часткових замін
        sorted_commands = sorted(self._punctuation.keys(), key=len, reverse=True)

        for command in sorted_commands:
            replacement = self._punctuation[command]

            # Шукаємо команду як окреме слово/фразу (case-insensitive)
            pattern = re.compile(r"\b" + re.escape(command) + r"\b", re.IGNORECASE)

            if replacement in ".,:;!?":
                # "текст крапка наступне" -> "текст. наступне"
                # Прибираємо пробіл перед знаком, зберігаємо пробіл після
                result = pattern.sub(replacement, result)
                result = re.sub(r"\s+([.,:;!?])", r"\1", result)
            elif replacement in ("(", ")", '"'):
                result = pattern.sub(replacement, result)
            else:
                result = pattern.sub(replacement, result)

        return result

    def _apply_dictionary(self, text: str, dictionary: dict[str, str]) -> str:
        """Застосовує словник замін до тексту."""
        result = text

        # Сортуємо за довжиною (довші спочатку)
        sorted_keys = sorted(dictionary.keys(), key=len, reverse=True)

        for spoken in sorted_keys:
            written = dictionary[spoken]
            # Заміна з урахуванням меж слів (case-insensitive)
            pattern = re.compile(r"\b" + re.escape(spoken) + r"\b", re.IGNORECASE)
            result = pattern.sub(written, result)

        return result

    def _capitalize(self, text: str) -> str:
        """Авто-капіталізація після крапок та на початку тексту."""
        if not text:
            return text

        # Капіталізація першого символу
        result = text[0].upper() + text[1:] if text else text

        # Капіталізація після . ! ? та нового рядка
        result = re.sub(
            r"([.!?]\s+)(\w)",
            lambda m: m.group(1) + m.group(2).upper(),
            result,
        )
        result = re.sub(
            r"(\n\s*)(\w)",
            lambda m: m.group(1) + m.group(2).upper(),
            result,
        )

        return result

    def _add_period(self, text: str) -> str:
        """Додає крапку в кінці тексту якщо немає іншої пунктуації."""
        if not text:
            return text

        stripped = text.rstrip()
        if stripped and stripped[-1] not in '.!?,;:-)"\n':
            return stripped + "."
        return stripped
