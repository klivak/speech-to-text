"""Тести для DictionaryManager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.constants import DEFAULT_DICTIONARY
from src.core.dictionary import DictionaryManager


class TestDictionaryManager:
    """Тести менеджера словника."""

    def test_creates_default_dictionary(self, dictionary_path: str) -> None:
        """Створює дефолтний словник якщо файл не існує."""
        dm = DictionaryManager(dictionary_path)
        assert Path(dictionary_path).exists()
        assert len(dm) > 0
        assert dm.dictionary.get("flutter") == "Flutter"

    def test_loads_existing_dictionary(self, dictionary_path: str) -> None:
        """Завантажує існуючий словник та мерджить дефолти."""
        custom = {"myword": "MyWord"}
        with open(dictionary_path, "w") as f:
            json.dump(custom, f)

        dm = DictionaryManager(dictionary_path)
        assert dm.dictionary.get("myword") == "MyWord"
        # Дефолтні записи автоматично додаються
        assert dm.dictionary.get("flutter") == "Flutter"

    def test_add_word(self, dictionary_path: str) -> None:
        """Додає слово до словника."""
        dm = DictionaryManager(dictionary_path)
        dm.add_word("тест", "Test")
        assert dm.dictionary["тест"] == "Test"

        # Перезавантажуємо та перевіряємо збереження
        dm2 = DictionaryManager(dictionary_path)
        assert dm2.dictionary["тест"] == "Test"

    def test_remove_word(self, dictionary_path: str) -> None:
        """Видаляє слово зі словника."""
        dm = DictionaryManager(dictionary_path)
        dm.add_word("тест", "Test")
        assert dm.remove_word("тест")
        assert "тест" not in dm.dictionary

    def test_remove_nonexistent_word(self, dictionary_path: str) -> None:
        """Повертає False при видаленні неіснуючого слова."""
        dm = DictionaryManager(dictionary_path)
        assert not dm.remove_word("nonexistent_word_xyz")

    def test_update_word(self, dictionary_path: str) -> None:
        """Оновлює запис у словнику."""
        dm = DictionaryManager(dictionary_path)
        dm.add_word("тест", "Test")
        dm.update_word("тест", "TEST")
        assert dm.dictionary["тест"] == "TEST"

    def test_reset_to_defaults(self, dictionary_path: str) -> None:
        """Скидає до дефолтних значень."""
        dm = DictionaryManager(dictionary_path)
        dm.add_word("custom", "Custom")
        dm.reset_to_defaults()
        assert "custom" not in dm.dictionary
        assert dm.dictionary.get("flutter") == "Flutter"

    def test_search(self, dictionary_path: str) -> None:
        """Пошук по словнику."""
        dm = DictionaryManager(dictionary_path)
        results = dm.search("flutter")
        assert len(results) > 0

    def test_import_from_file(self, dictionary_path: str, temp_dir: Path) -> None:
        """Імпорт словника з файлу."""
        dm = DictionaryManager(dictionary_path)

        import_file = temp_dir / "import.json"
        with open(import_file, "w") as f:
            json.dump({"imported": "Imported"}, f)

        success, message = dm.import_from_file(str(import_file))
        assert success
        assert dm.dictionary.get("imported") == "Imported"

    def test_export_to_file(self, dictionary_path: str, temp_dir: Path) -> None:
        """Експорт словника в файл."""
        dm = DictionaryManager(dictionary_path)
        export_file = temp_dir / "export.json"

        success, message = dm.export_to_file(str(export_file))
        assert success
        assert export_file.exists()

        with open(export_file, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_import_invalid_file(self, dictionary_path: str, temp_dir: Path) -> None:
        """Імпорт невалідного файлу."""
        dm = DictionaryManager(dictionary_path)
        bad_file = temp_dir / "bad.json"
        with open(bad_file, "w") as f:
            f.write("{invalid")

        success, message = dm.import_from_file(str(bad_file))
        assert not success

    def test_case_insensitive_add(self, dictionary_path: str) -> None:
        """Ключі словника зберігаються в нижньому регістрі."""
        dm = DictionaryManager(dictionary_path)
        dm.add_word("MyWord", "MyWord")
        assert "myword" in dm.dictionary

    def test_auto_merge_preserves_user_entries(self, dictionary_path: str) -> None:
        """Авто-мерж не перезаписує користувацькі значення."""
        custom = {"flutter": "MyCustomFlutter", "myterm": "MyTerm"}
        with open(dictionary_path, "w") as f:
            json.dump(custom, f)

        dm = DictionaryManager(dictionary_path)
        # Користувацьке значення збережено
        assert dm.dictionary["flutter"] == "MyCustomFlutter"
        # Нові дефолтні записи додані
        assert dm.dictionary.get("myterm") == "MyTerm"
        assert "dart" in dm.dictionary
