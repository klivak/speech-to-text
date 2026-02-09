"""Тести для HistoryManager."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.history import HistoryManager
from src.core.transcriber import TranscriptionResult


def _make_result(text: str = "тестовий текст", language: str = "uk") -> TranscriptionResult:
    """Створює тестовий результат розпізнавання."""
    return TranscriptionResult(
        text=text,
        language=language,
        duration=2.0,
        processing_time=0.5,
        mode="local",
        model="small",
        device="cpu",
    )


class TestHistoryManager:
    """Тести менеджера історії."""

    def test_creates_empty_history(self, history_path: str) -> None:
        """Створює порожню історію."""
        hm = HistoryManager(history_path)
        assert len(hm) == 0

    def test_add_entry(self, history_path: str) -> None:
        """Додає запис в історію."""
        hm = HistoryManager(history_path)
        hm.add(_make_result())
        assert len(hm) == 1
        assert hm.entries[0].text == "тестовий текст"

    def test_add_preserves_order(self, history_path: str) -> None:
        """Нові записи додаються на початок."""
        hm = HistoryManager(history_path)
        hm.add(_make_result("перший"))
        hm.add(_make_result("другий"))
        assert hm.entries[0].text == "другий"
        assert hm.entries[1].text == "перший"

    def test_skip_empty_results(self, history_path: str) -> None:
        """Не додає порожні результати."""
        hm = HistoryManager(history_path)
        hm.add(_make_result(""))
        hm.add(_make_result("   "))
        assert len(hm) == 0

    def test_max_items_limit(self, history_path: str) -> None:
        """Обмежує кількість записів."""
        hm = HistoryManager(history_path, max_items=5)
        for i in range(10):
            hm.add(_make_result(f"запис {i}"))
        assert len(hm) == 5

    def test_persistence(self, history_path: str) -> None:
        """Історія зберігається між сесіями."""
        hm1 = HistoryManager(history_path)
        hm1.add(_make_result("збережений текст"))

        hm2 = HistoryManager(history_path)
        assert len(hm2) == 1
        assert hm2.entries[0].text == "збережений текст"

    def test_search(self, history_path: str) -> None:
        """Пошук по тексту."""
        hm = HistoryManager(history_path)
        hm.add(_make_result("Python programming"))
        hm.add(_make_result("JavaScript development"))
        hm.add(_make_result("Python is great"))

        results = hm.search("Python")
        assert len(results) == 2

    def test_search_case_insensitive(self, history_path: str) -> None:
        """Пошук без урахування регістру."""
        hm = HistoryManager(history_path)
        hm.add(_make_result("Python"))
        results = hm.search("python")
        assert len(results) == 1

    def test_delete(self, history_path: str) -> None:
        """Видалення запису за індексом."""
        hm = HistoryManager(history_path)
        hm.add(_make_result("перший"))
        hm.add(_make_result("другий"))

        assert hm.delete(0)
        assert len(hm) == 1
        assert hm.entries[0].text == "перший"

    def test_delete_invalid_index(self, history_path: str) -> None:
        """Видалення з невалідним індексом."""
        hm = HistoryManager(history_path)
        assert not hm.delete(0)
        assert not hm.delete(-1)

    def test_clear(self, history_path: str) -> None:
        """Очищення історії."""
        hm = HistoryManager(history_path)
        hm.add(_make_result("текст"))
        hm.clear()
        assert len(hm) == 0

    def test_export_to_txt(self, history_path: str, temp_dir: Path) -> None:
        """Експорт в текстовий файл."""
        hm = HistoryManager(history_path)
        hm.add(_make_result("тестовий текст"))

        export_path = str(temp_dir / "export.txt")
        success, message = hm.export_to_txt(export_path)
        assert success
        assert Path(export_path).exists()

        with open(export_path, encoding="utf-8") as f:
            content = f.read()
        assert "тестовий текст" in content

    def test_statistics(self, history_path: str) -> None:
        """Статистика історії."""
        hm = HistoryManager(history_path)
        hm.add(_make_result("текст 1", "uk"))
        hm.add(_make_result("text 2", "en"))
        hm.add(_make_result("текст 3", "uk"))

        assert hm.get_total_count() == 3
        assert hm.get_total_audio_duration() == pytest.approx(6.0)
        assert hm.get_average_processing_time() == pytest.approx(0.5)
        assert hm.get_most_used_language() == "uk"

    def test_daily_counts(self, history_path: str) -> None:
        """Кількість розпізнавань за дні."""
        hm = HistoryManager(history_path)
        hm.add(_make_result("текст"))

        daily = hm.get_daily_counts(7)
        assert len(daily) == 7
        assert all(isinstance(d, tuple) and len(d) == 2 for d in daily)
