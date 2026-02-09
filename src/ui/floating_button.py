"""Плаваюча кнопка мікрофона -- альтернатива гарячій клавіші."""

from __future__ import annotations

import math

from PyQt6.QtCore import QPoint, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QApplication, QMenu, QWidget

from src.constants import FLOAT_BUTTON_SIZES


class FloatingMicButton(QWidget):
    """Плаваюча кнопка мікрофона.

    Маленька кругла кнопка що завжди поверх вікон.
    Можна перетягнути в будь-яке місце екрану.

    Сигнали:
        clicked: натискання кнопки (старт/стоп запису)
        settings_requested: запит на відкриття налаштувань
        hide_requested: запит на приховування кнопки
    """

    clicked = pyqtSignal()
    settings_requested = pyqtSignal()
    hide_requested = pyqtSignal()

    def __init__(
        self,
        size: str = "medium",
        position_x: int = -1,
        position_y: int = -1,
        is_dark_theme: bool = True,
    ) -> None:
        super().__init__(None)

        self._btn_size = FLOAT_BUTTON_SIZES.get(size, 48)
        self._is_recording = False
        self._is_hovered = False
        self._is_dark = is_dark_theme
        self._pulse_phase = 0.0

        # Drag & drop
        self._dragging = False
        self._drag_offset = QPoint()

        # Анімація пульсації при записі
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_animate)
        self._pulse_timer.setInterval(30)

        # Налаштування вікна
        self.setFixedSize(self._btn_size + 10, self._btn_size + 10)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Позиція
        if position_x >= 0 and position_y >= 0:
            self.move(position_x, position_y)
        else:
            self._default_position()

    def update_settings(
        self,
        size: str | None = None,
        is_dark_theme: bool | None = None,
    ) -> None:
        """Оновлює налаштування кнопки."""
        if size is not None:
            self._btn_size = FLOAT_BUTTON_SIZES.get(size, 48)
            self.setFixedSize(self._btn_size + 10, self._btn_size + 10)
        if is_dark_theme is not None:
            self._is_dark = is_dark_theme
        self.update()

    def set_recording(self, recording: bool) -> None:
        """Встановлює стан запису."""
        self._is_recording = recording
        if recording:
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self._pulse_phase = 0.0
        self.update()

    def get_position(self) -> tuple[int, int]:
        """Повертає поточну позицію кнопки."""
        pos = self.pos()
        return pos.x(), pos.y()

    def _default_position(self) -> None:
        """Позиціонує кнопку в правий нижній кут."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            x = geo.width() - self._btn_size - 40
            y = geo.height() - self._btn_size - 100
            self.move(x, y)

    def _pulse_animate(self) -> None:
        """Анімація пульсації."""
        self._pulse_phase += 0.1
        if self._pulse_phase > math.pi * 2:
            self._pulse_phase -= math.pi * 2
        self.update()

    # --- Події ---

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Малювання кнопки."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        cy = self.height() / 2
        radius = self._btn_size / 2

        # Фон кнопки
        if self._is_recording:
            # Пульсуюче червоне свічення
            pulse = math.sin(self._pulse_phase) * 0.15
            glow_r = radius * (1.3 + pulse)
            glow = QRadialGradient(cx, cy, glow_r)
            glow_color = QColor(244, 67, 54, 60)
            glow.setColorAt(0.0, glow_color)
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

            # Червоне коло
            bg_color = QColor(244, 67, 54)
        elif self._is_hovered:
            bg_color = QColor(124, 110, 240) if self._is_dark else QColor(103, 80, 164)
        else:
            # Напівпрозоре
            if self._is_dark:
                bg_color = QColor(60, 60, 80, 200)
            else:
                bg_color = QColor(240, 240, 250, 220)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Іконка мікрофона (спрощена)
        if self._is_dark or self._is_recording or self._is_hovered:
            icon_color = QColor(255, 255, 255)
        else:
            icon_color = QColor(80, 80, 100)

        pen = QPen(icon_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(icon_color))

        # Корпус мікрофона (прямокутник з заокругленими кутами)
        mic_w = radius * 0.35
        mic_h = radius * 0.55
        mic_rect = QRectF(cx - mic_w, cy - mic_h, mic_w * 2, mic_h * 1.6)
        painter.drawRoundedRect(mic_rect, mic_w, mic_w)

        # Дуга під мікрофоном
        painter.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRectF(cx - mic_w * 1.5, cy - mic_h * 0.3, mic_w * 3, mic_h * 1.8)
        painter.drawArc(arc_rect, -180 * 16, 180 * 16)

        # Ніжка
        painter.drawLine(int(cx), int(cy + mic_h * 0.75), int(cx), int(cy + mic_h * 1.0))
        # Основа
        painter.drawLine(
            int(cx - mic_w * 0.8),
            int(cy + mic_h * 1.0),
            int(cx + mic_w * 0.8),
            int(cy + mic_h * 1.0),
        )

        painter.end()

    def enterEvent(self, event: object) -> None:  # type: ignore[override]  # noqa: N802
        """Курсор над кнопкою."""
        self._is_hovered = True
        self.update()

    def leaveEvent(self, event: object) -> None:  # type: ignore[override]  # noqa: N802
        """Курсор залишив кнопку."""
        self._is_hovered = False
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Натискання миші."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.position().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Переміщення миші (перетягування)."""
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Відпускання миші."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                # Перевіряємо чи це був клік (не перетягування)
                delta = event.position().toPoint() - self._drag_offset
                if abs(delta.x()) < 5 and abs(delta.y()) < 5:
                    self.clicked.emit()
            self._dragging = False

    def _show_context_menu(self, pos: QPoint) -> None:
        """Показує контекстне меню."""
        menu = QMenu(self)
        menu.addAction("Налаштування", self.settings_requested.emit)
        menu.addSeparator()
        menu.addAction("Сховати кнопку", self.hide_requested.emit)
        menu.exec(pos)
