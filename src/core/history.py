"""Менеджер історії розпізнавань."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from src.constants import MAX_HISTORY_ITEMS
from src.core.transcriber import TranscriptionResult

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """Запис в історії розпізнавань."""

    text: str
    language: str
    mode: str
    model: str
    duration: float
    processing_time: float
    timestamp: float = field(default_factory=time.time)
    device: str = ""

    def to_dict(self) -> dict:
        """Конвертує в словник для JSON."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> HistoryEntry:
        """Створює з словника."""
        return HistoryEntry(
            text=data.get("text", ""),
            language=data.get("language", ""),
            mode=data.get("mode", ""),
            model=data.get("model", ""),
            duration=data.get("duration", 0.0),
            processing_time=data.get("processing_time", 0.0),
            timestamp=data.get("timestamp", 0.0),
            device=data.get("device", ""),
        )

    @staticmethod
    def from_result(result: TranscriptionResult) -> HistoryEntry:
        """Створює з результату розпізнавання."""
        return HistoryEntry(
            text=result.text,
            language=result.language,
            mode=result.mode,
            model=result.model,
            duration=result.duration,
            processing_time=result.processing_time,
            timestamp=result.timestamp,
            device=result.device,
        )


class HistoryManager:
    """Менеджер історії розпізнавань з збереженням в JSON."""

    def __init__(
        self,
        history_path: str = "history.json",
        max_items: int = MAX_HISTORY_ITEMS,
    ) -> None:
        self._path = Path(history_path)
        self._max_items = max_items
        self._entries: list[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        """Завантажує історію з файлу."""
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    data = json.load(f)
                self._entries = [HistoryEntry.from_dict(item) for item in data]
                logger.info("Історію завантажено: %d записів.", len(self._entries))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Помилка читання історії: %s", e)
                self._entries = []
        else:
            self._entries = []

    def _save(self) -> None:
        """Зберігає історію у файл."""
        try:
            data = [entry.to_dict() for entry in self._entries]
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error("Помилка збереження історії: %s", e)

    def add(self, result: TranscriptionResult) -> None:
        """Додає результат розпізнавання в історію."""
        if result.is_empty:
            return

        entry = HistoryEntry.from_result(result)
        self._entries.insert(0, entry)

        # Обмежуємо кількість записів
        if len(self._entries) > self._max_items:
            self._entries = self._entries[: self._max_items]

        self._save()

    @property
    def entries(self) -> list[HistoryEntry]:
        """Всі записи історії (новіші спочатку)."""
        return list(self._entries)

    def search(self, query: str) -> list[HistoryEntry]:
        """Пошук по тексту в історії."""
        query_lower = query.lower()
        return [e for e in self._entries if query_lower in e.text.lower()]

    def delete(self, index: int) -> bool:
        """Видаляє запис за індексом."""
        if 0 <= index < len(self._entries):
            self._entries.pop(index)
            self._save()
            return True
        return False

    def clear(self) -> None:
        """Очищає всю історію."""
        self._entries.clear()
        self._save()
        logger.info("Історію очищено.")

    def export_to_txt(self, file_path: str) -> tuple[bool, str]:
        """Експортує історію в текстовий файл."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for entry in self._entries:
                    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry.timestamp))
                    f.write(f"[{ts}] [{entry.language}] [{entry.mode}]\n")
                    f.write(f"{entry.text}\n")
                    f.write(f"(Тривалість: {entry.duration:.1f}с, ")
                    f.write(f"Обробка: {entry.processing_time:.1f}с)\n")
                    f.write("-" * 60 + "\n")
            return True, f"Експортовано {len(self._entries)} записів."
        except OSError as e:
            return False, f"Помилка експорту: {e}"

    # Статистика

    def get_total_count(self) -> int:
        """Загальна кількість розпізнавань."""
        return len(self._entries)

    def get_today_count(self) -> int:
        """Кількість розпізнавань сьогодні."""
        today_start = time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d"))
        return sum(1 for e in self._entries if e.timestamp >= today_start)

    def get_total_audio_duration(self) -> float:
        """Загальна тривалість аудіо в секундах."""
        return sum(e.duration for e in self._entries)

    def get_average_processing_time(self) -> float:
        """Середній час обробки."""
        if not self._entries:
            return 0.0
        return sum(e.processing_time for e in self._entries) / len(self._entries)

    def get_most_used_language(self) -> str:
        """Найпопулярніша мова."""
        if not self._entries:
            return ""
        lang_counts: dict[str, int] = {}
        for e in self._entries:
            lang_counts[e.language] = lang_counts.get(e.language, 0) + 1
        return max(lang_counts, key=lang_counts.get)  # type: ignore[arg-type]

    def get_daily_counts(self, days: int = 7) -> list[tuple[str, int]]:
        """Кількість розпізнавань за останні N днів."""
        result: list[tuple[str, int]] = []
        now = time.time()

        for i in range(days - 1, -1, -1):
            day_start = now - (i + 1) * 86400
            day_end = now - i * 86400
            date_str = time.strftime("%d.%m", time.localtime(day_end))
            count = sum(1 for e in self._entries if day_start <= e.timestamp < day_end)
            result.append((date_str, count))

        return result

    def __len__(self) -> int:
        return len(self._entries)
