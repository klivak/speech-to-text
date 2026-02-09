"""Вікно історії розпізнавань."""

from __future__ import annotations

import time

import pyperclip
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.constants import SUPPORTED_LANGUAGES
from src.core.history import HistoryEntry


class HistoryWindow(QDialog):
    """Вікно перегляду та пошуку в історії розпізнавань.

    Сигнали:
        entry_deleted: int -- видалення запису за індексом
        history_cleared: очищення всієї історії
        export_requested: str -- експорт в файл
    """

    entry_deleted = pyqtSignal(int)
    history_cleared = pyqtSignal()
    export_requested = pyqtSignal(str)

    def __init__(self, entries: list[HistoryEntry], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entries = entries

        self.setWindowTitle("VoiceType -- Iсторiя розпiзнавань")
        self.setMinimumSize(700, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._setup_ui()
        self._load_entries()

    def _setup_ui(self) -> None:
        """Створює інтерфейс вікна."""
        layout = QVBoxLayout(self)

        # Пошук
        search_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Пошук по тексту...")
        self._search_input.textChanged.connect(self._filter_entries)
        search_layout.addWidget(self._search_input)

        self._count_label = QLabel("0 записiв")
        search_layout.addWidget(self._count_label)
        layout.addLayout(search_layout)

        # Таблиця
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["Час", "Мова", "Режим", "Обробка", "Текст", ""])
        header = self._table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        # Кнопки внизу
        btn_layout = QHBoxLayout()

        export_btn = QPushButton("Експорт в TXT")
        export_btn.clicked.connect(self._export)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        clear_btn = QPushButton("Очистити iсторiю")
        clear_btn.setProperty("flat", True)
        clear_btn.clicked.connect(self._clear_history)
        btn_layout.addWidget(clear_btn)

        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_entries(self) -> None:
        """Завантажує записи в таблицю."""
        self._table.setRowCount(0)

        for i, entry in enumerate(self._entries):
            self._add_entry_row(i, entry)

        self._count_label.setText(f"{len(self._entries)} записiв")

    def _add_entry_row(self, index: int, entry: HistoryEntry) -> None:
        """Додає рядок запису в таблицю."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Час
        ts = time.strftime("%d.%m.%Y %H:%M", time.localtime(entry.timestamp))
        self._table.setItem(row, 0, QTableWidgetItem(ts))

        # Мова
        lang_name = SUPPORTED_LANGUAGES.get(entry.language, entry.language)
        self._table.setItem(row, 1, QTableWidgetItem(lang_name))

        # Режим
        mode_text = "API" if entry.mode == "api" else f"Локальний ({entry.model})"
        self._table.setItem(row, 2, QTableWidgetItem(mode_text))

        # Час обробки
        self._table.setItem(row, 3, QTableWidgetItem(f"{entry.processing_time:.1f}с"))

        # Текст
        text_preview = entry.text[:80] + "..." if len(entry.text) > 80 else entry.text
        text_item = QTableWidgetItem(text_preview)
        text_item.setToolTip(entry.text)
        self._table.setItem(row, 4, text_item)

        # Кнопки
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(2, 2, 2, 2)

        copy_btn = QPushButton("Копiювати")
        copy_btn.setFixedWidth(80)
        copy_btn.clicked.connect(lambda checked, t=entry.text: pyperclip.copy(t))
        btn_layout.addWidget(copy_btn)

        del_btn = QPushButton("X")
        del_btn.setFixedWidth(30)
        del_btn.clicked.connect(lambda checked, idx=index: self._delete_entry(idx))
        btn_layout.addWidget(del_btn)

        self._table.setCellWidget(row, 5, btn_widget)

    def _filter_entries(self, query: str) -> None:
        """Фільтрує записи за пошуковим запитом."""
        query_lower = query.lower()
        self._table.setRowCount(0)

        filtered = [
            (i, e)
            for i, e in enumerate(self._entries)
            if not query_lower or query_lower in e.text.lower()
        ]

        for i, entry in filtered:
            self._add_entry_row(i, entry)

        self._count_label.setText(f"{len(filtered)} записiв")

    def _delete_entry(self, index: int) -> None:
        """Видаляє запис за оригінальним індексом."""
        if 0 <= index < len(self._entries):
            self.entry_deleted.emit(index)
            self._entries.pop(index)
            # Перезавантажуємо з урахуванням активного фільтру
            self._filter_entries(self._search_input.text())

    def _clear_history(self) -> None:
        """Очищає всю історію з підтвердженням."""
        reply = QMessageBox.question(
            self,
            "Очистити iсторiю",
            "Ви впевненi що хочете видалити всю iсторiю розпiзнавань?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_cleared.emit()
            self._entries.clear()
            self._load_entries()

    def _export(self) -> None:
        """Експортує історію в TXT файл."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Експорт iсторiї", "voicetype_history.txt", "Text (*.txt)"
        )
        if file_path:
            self.export_requested.emit(file_path)
