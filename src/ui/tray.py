"""Системний трей -- іконка та контекстне меню."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtCore import QRect, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.constants import APP_NAME, APP_VERSION, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)


def _get_assets_dir() -> Path:
    """Повертає шлях до директорії assets."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets"  # type: ignore[attr-defined]
    return Path(__file__).parent.parent.parent / "assets"


def _create_colored_icon(color: QColor, size: int = 64) -> QIcon:
    """Створює стилізовану іконку EchoScribe з пером та звуковими хвилями."""
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QLinearGradient, QPainterPath, QPen

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Фонове коло з градієнтом
    margin = 2
    gradient = QLinearGradient(QPointF(0, 0), QPointF(size, size))
    gradient.setColorAt(0, color)
    gradient.setColorAt(1, color.darker(130))
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRect(margin, margin, size - margin * 2, size - margin * 2))

    # Перо (scribe) -- стилізоване
    pen_color = QColor(255, 255, 255)
    painter.setPen(QPen(pen_color, size * 0.04, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(QBrush(pen_color))

    cx = size * 0.38
    cy = size * 0.55
    pen_path = QPainterPath()
    pen_path.moveTo(cx - size * 0.08, cy + size * 0.18)
    pen_path.lineTo(cx + size * 0.12, cy - size * 0.22)
    pen_path.lineTo(cx + size * 0.16, cy - size * 0.18)
    pen_path.lineTo(cx - size * 0.04, cy + size * 0.22)
    pen_path.closeSubpath()
    painter.drawPath(pen_path)

    # Звукові хвилі (echo) -- 3 дуги справа
    wave_color = QColor(255, 255, 255, 200)
    wave_cx = size * 0.6
    wave_cy = size * 0.45

    for i, radius in enumerate([size * 0.1, size * 0.17, size * 0.24]):
        alpha = 200 - i * 50
        wave_color.setAlpha(alpha)
        painter.setPen(
            QPen(wave_color, size * 0.035, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRect(
            int(wave_cx - radius),
            int(wave_cy - radius),
            int(radius * 2),
            int(radius * 2),
        )
        painter.drawArc(arc_rect, -45 * 16, 90 * 16)

    painter.end()
    return QIcon(pixmap)


class SystemTray(QSystemTrayIcon):
    """Іконка та меню в системному треї Windows.

    Сигнали:
        settings_requested: відкрити налаштування
        history_requested: відкрити історію
        toggle_enabled: перемкнути активність
        language_changed: зміна мови (str)
        device_changed: зміна пристрою (str)
        check_updates_requested: перевірити оновлення
        quit_requested: вихід з програми
    """

    settings_requested = pyqtSignal()
    history_requested = pyqtSignal()
    toggle_enabled = pyqtSignal()
    language_changed = pyqtSignal(str)
    device_changed = pyqtSignal(str)
    check_updates_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(
        self,
        parent: QApplication | None = None,
        mode: str = "local",
        model: str = "small",
        language: str = "uk",
        device: str = "cpu",
    ) -> None:
        # Створюємо іконку програмно
        self._normal_icon = _create_colored_icon(QColor(124, 110, 240))
        self._recording_icon = _create_colored_icon(QColor(244, 67, 54))

        super().__init__(self._normal_icon, parent)

        self._is_enabled = True
        self._mode = mode
        self._model = model
        self._language = language
        self._device = device

        self._setup_menu()
        self._update_tooltip()

        # Подвійний клік -- відкрити налаштування
        self.activated.connect(self._on_activated)

    def _setup_menu(self) -> None:
        """Створює контекстне меню трею."""
        self._menu = QMenu()

        # Стан
        self._enable_action = QAction("Увімкнено", self._menu)
        self._enable_action.setCheckable(True)
        self._enable_action.setChecked(self._is_enabled)
        self._enable_action.triggered.connect(self.toggle_enabled.emit)
        self._menu.addAction(self._enable_action)

        self._menu.addSeparator()

        # Мова
        lang_menu = self._menu.addMenu("Мова")
        assert lang_menu is not None
        self._lang_actions: dict[str, QAction] = {}
        for code, name in SUPPORTED_LANGUAGES.items():
            action = QAction(name, lang_menu)
            action.setCheckable(True)
            action.setChecked(code == self._language)
            action.triggered.connect(lambda checked, c=code: self._on_language_change(c))
            lang_menu.addAction(action)
            self._lang_actions[code] = action

        # Пристрій (тільки для локального режиму)
        self._device_menu = self._menu.addMenu("Пристрій")
        assert self._device_menu is not None
        self._cpu_action = QAction("CPU", self._device_menu)
        self._cpu_action.setCheckable(True)
        self._cpu_action.setChecked(self._device == "cpu")
        self._cpu_action.triggered.connect(lambda: self._on_device_change("cpu"))
        self._device_menu.addAction(self._cpu_action)

        self._gpu_action = QAction("GPU (CUDA)", self._device_menu)
        self._gpu_action.setCheckable(True)
        self._gpu_action.setChecked(self._device == "cuda")
        self._gpu_action.triggered.connect(lambda: self._on_device_change("cuda"))
        self._device_menu.addAction(self._gpu_action)

        self._device_menu.setEnabled(self._mode == "local")

        self._menu.addSeparator()

        # Дії
        settings_action = QAction("Налаштування", self._menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        self._menu.addAction(settings_action)

        history_action = QAction("Iсторiя розпiзнавань", self._menu)
        history_action.triggered.connect(self.history_requested.emit)
        self._menu.addAction(history_action)

        self._menu.addSeparator()

        update_action = QAction("Перевiрити оновлення", self._menu)
        update_action.triggered.connect(self.check_updates_requested.emit)
        self._menu.addAction(update_action)

        about_action = QAction(f"Про {APP_NAME} v{APP_VERSION}", self._menu)
        about_action.triggered.connect(self._show_about)
        self._menu.addAction(about_action)

        self._menu.addSeparator()

        quit_action = QAction("Вихiд", self._menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(quit_action)

        self.setContextMenu(self._menu)

    def _update_tooltip(self) -> None:
        """Оновлює тултіп іконки трею."""
        lang_name = SUPPORTED_LANGUAGES.get(self._language, self._language)
        if self._mode == "local":
            tooltip = (
                f"{APP_NAME} | Локальний | {self._model} | {lang_name} | {self._device.upper()}"
            )
        else:
            tooltip = f"{APP_NAME} | API | {lang_name}"
        self.setToolTip(tooltip)

    def set_recording(self, recording: bool) -> None:
        """Змінює іконку при записі."""
        if recording:
            self.setIcon(self._recording_icon)
        else:
            self.setIcon(self._normal_icon)

    def update_state(
        self,
        mode: str | None = None,
        model: str | None = None,
        language: str | None = None,
        device: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        """Оновлює стан трею."""
        if mode is not None:
            self._mode = mode
            self._device_menu.setEnabled(mode == "local")  # type: ignore[union-attr]
        if model is not None:
            self._model = model
        if language is not None:
            self._language = language
            for code, action in self._lang_actions.items():
                action.setChecked(code == language)
        if device is not None:
            self._device = device
            self._cpu_action.setChecked(device == "cpu")
            self._gpu_action.setChecked(device == "cuda")
        if enabled is not None:
            self._is_enabled = enabled
            self._enable_action.setChecked(enabled)

        self._update_tooltip()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Обробник активації іконки трею."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()

    def _on_language_change(self, language: str) -> None:
        """Обробник зміни мови."""
        self._language = language
        for code, action in self._lang_actions.items():
            action.setChecked(code == language)
        self._update_tooltip()
        self.language_changed.emit(language)

    def _on_device_change(self, device: str) -> None:
        """Обробник зміни пристрою."""
        self._device = device
        self._cpu_action.setChecked(device == "cpu")
        self._gpu_action.setChecked(device == "cuda")
        self._update_tooltip()
        self.device_changed.emit(device)

    def _show_about(self) -> None:
        """Показує діалог 'Про програму'."""
        from PyQt6.QtWidgets import QMessageBox

        msg = QMessageBox()
        msg.setWindowTitle(f"Про {APP_NAME}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            f"<p>Голосовий ввiд тексту для Windows на базi OpenAI Whisper.</p>"
            f"<p>Тримай гарячу клавiшу, говори, вiдпусти -- текст миттєво "
            f"вставляється в будь-яку програму.</p>"
            f"<p><b>Безпека:</b> API ключi зберiгаються в Windows Credential Manager. "
            f"Данi нiкуди не вiдправляються (крiм OpenAI API в режимi API). "
            f"Аудiо та текст обробляються локально.</p>"
            f'<p><a href="https://github.com/klivak/speech-to-text">GitHub</a></p>'
        )
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.addButton("Ок", QMessageBox.ButtonRole.AcceptRole)

        # Іконка вікна
        msg.setWindowIcon(_create_colored_icon(QColor(124, 110, 240)))

        msg.exec()
