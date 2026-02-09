"""Менеджер кастомного словника технічних термінів."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.constants import DEFAULT_DICTIONARY

logger = logging.getLogger(__name__)


class DictionaryManager:
    """Менеджер словника для покращення розпізнавання технічних термінів.

    Словник зберігається в JSON файлі та застосовується після розпізнавання
    Whisper для заміни неправильно розпізнаних технічних термінів.
    """

    def __init__(self, dictionary_path: str = "dictionary.json") -> None:
        self._path = Path(dictionary_path)
        self._dictionary: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Завантажує словник з файлу або створює дефолтний."""
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    self._dictionary = json.load(f)
                logger.info("Словник завантажено: %d записів.", len(self._dictionary))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Помилка читання словника: %s. Використовуємо дефолтний.", e)
                self._dictionary = dict(DEFAULT_DICTIONARY)
                self._save()
        else:
            logger.info("Файл словника не знайдено, створюємо дефолтний.")
            self._dictionary = dict(DEFAULT_DICTIONARY)
            self._save()

    def _save(self) -> None:
        """Зберігає словник у файл."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._dictionary, f, indent=2, ensure_ascii=False)
            logger.debug("Словник збережено: %d записів.", len(self._dictionary))
        except OSError as e:
            logger.error("Помилка збереження словника: %s", e)

    @property
    def dictionary(self) -> dict[str, str]:
        """Копія поточного словника."""
        return dict(self._dictionary)

    def add_word(self, spoken: str, written: str) -> None:
        """Додає слово до словника."""
        self._dictionary[spoken.lower()] = written
        self._save()
        logger.debug("Додано до словника: '%s' -> '%s'", spoken, written)

    def remove_word(self, spoken: str) -> bool:
        """Видаляє слово зі словника. Повертає True якщо слово було знайдено."""
        key = spoken.lower()
        if key in self._dictionary:
            del self._dictionary[key]
            self._save()
            logger.debug("Видалено зі словника: '%s'", spoken)
            return True
        return False

    def update_word(self, spoken: str, written: str) -> None:
        """Оновлює запис у словнику."""
        self._dictionary[spoken.lower()] = written
        self._save()

    def reset_to_defaults(self) -> None:
        """Скидає словник до дефолтних значень."""
        self._dictionary = dict(DEFAULT_DICTIONARY)
        self._save()
        logger.info("Словник скинуто до дефолтних значень.")

    def import_from_file(self, file_path: str) -> tuple[bool, str]:
        """Імпортує словник з JSON файлу.

        Повертає (успіх, повідомлення).
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return False, "Файл має містити JSON об'єкт (словник)."

            count = 0
            for spoken, written in data.items():
                if isinstance(spoken, str) and isinstance(written, str):
                    self._dictionary[spoken.lower()] = written
                    count += 1

            self._save()
            return True, f"Імпортовано {count} записів."
        except (json.JSONDecodeError, OSError) as e:
            return False, f"Помилка імпорту: {e}"

    def export_to_file(self, file_path: str) -> tuple[bool, str]:
        """Експортує словник в JSON файл.

        Повертає (успіх, повідомлення).
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._dictionary, f, indent=2, ensure_ascii=False)
            return True, f"Експортовано {len(self._dictionary)} записів."
        except OSError as e:
            return False, f"Помилка експорту: {e}"

    def search(self, query: str) -> dict[str, str]:
        """Пошук по словнику."""
        query_lower = query.lower()
        return {
            k: v
            for k, v in self._dictionary.items()
            if query_lower in k.lower() or query_lower in v.lower()
        }

    def __len__(self) -> int:
        return len(self._dictionary)
