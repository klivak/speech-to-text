"""Візуальний оверлей при записі -- пульсуюче коло з візуалізацією амплітуди."""

from __future__ import annotations

import math
from enum import Enum, auto

from PyQt6.QtCore import QPoint, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPaintEvent,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QApplication, QWidget

from src.constants import OVERLAY_POSITIONS, OVERLAY_SIZES


class OverlayState(Enum):
    """Стани оверлею."""

    HIDDEN = auto()
    RECORDING = auto()
    PROCESSING = auto()
    SUCCESS = auto()
    ERROR = auto()


class RecordingOverlay(QWidget):
    """Напівпрозорий оверлей з пульсуючим колом для візуалізації запису.

    Відображається по центру екрану поверх усіх вікон.
    Клікабельний наскрізь -- не перехоплює фокус та кліки.
    """

    def __init__(
        self,
        size: str = "medium",
        position: str = "center",
        opacity: float = 0.8,
        show_text: bool = True,
    ) -> None:
        super().__init__(None)

        # Налаштування
        self._base_radius = OVERLAY_SIZES.get(size, 120)
        self._position = position
        self._opacity = opacity
        self._show_text = show_text

        # Стан
        self._state = OverlayState.HIDDEN
        self._amplitude = 0.0
        self._pulse_phase = 0.0
        self._result_text = ""
        self._error_text = ""

        # Таймер анімації (~60 FPS)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.setInterval(16)

        # Таймер автоприховування
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide_overlay)

        # Розмір вікна
        window_size = self._base_radius * 4
        self.setFixedSize(window_size, window_size)

        # Прапорці вікна: поверх усіх, без рамки, як інструмент
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )

        # Прозорий фон, клікабельний наскрізь
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def update_settings(
        self,
        size: str | None = None,
        position: str | None = None,
        opacity: float | None = None,
        show_text: bool | None = None,
    ) -> None:
        """Оновлює налаштування оверлею."""
        if size is not None:
            self._base_radius = OVERLAY_SIZES.get(size, 120)
            window_size = self._base_radius * 4
            self.setFixedSize(window_size, window_size)
        if position is not None:
            self._position = position
        if opacity is not None:
            self._opacity = opacity
        if show_text is not None:
            self._show_text = show_text

    def show_recording(self) -> None:
        """Показує оверлей в стані запису."""
        self._state = OverlayState.RECORDING
        self._amplitude = 0.0
        self._pulse_phase = 0.0
        self._position_on_screen()
        self.show()
        self._anim_timer.start()

    def show_processing(self) -> None:
        """Перемикає оверлей в стан обробки."""
        self._state = OverlayState.PROCESSING

    def show_success(self, text: str = "") -> None:
        """Показує стан успіху та автоматично ховає."""
        self._state = OverlayState.SUCCESS
        self._result_text = text[:60] if text else ""
        self._hide_timer.start(700)

    def show_error(self, message: str = "") -> None:
        """Показує стан помилки та автоматично ховає."""
        self._state = OverlayState.ERROR
        self._error_text = message[:40] if message else "Помилка"
        self._hide_timer.start(1500)

    def hide_overlay(self) -> None:
        """Ховає оверлей."""
        self._state = OverlayState.HIDDEN
        self._anim_timer.stop()
        self._hide_timer.stop()
        self.hide()

    def set_amplitude(self, amplitude: float) -> None:
        """Оновлює амплітуду для візуалізації (0.0 - 1.0)."""
        self._amplitude = max(0.0, min(1.0, amplitude))

    def preview(self, duration_ms: int = 3000) -> None:
        """Показує попередній перегляд оверлею."""
        self.show_recording()
        self._amplitude = 0.5
        self._hide_timer.start(duration_ms)

    def _position_on_screen(self) -> None:
        """Позиціонує оверлей на екрані."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return

        screen_geo = screen.geometry()
        x = (screen_geo.width() - self.width()) // 2
        y: int

        if self._position == "top_center":
            y = screen_geo.height() // 6
        elif self._position == "bottom_center":
            y = screen_geo.height() * 2 // 3
        else:  # center
            y = (screen_geo.height() - self.height()) // 2

        self.move(QPoint(x + screen_geo.x(), y + screen_geo.y()))

    def _animate(self) -> None:
        """Крок анімації."""
        self._pulse_phase += 0.05
        if self._pulse_phase > math.pi * 2:
            self._pulse_phase -= math.pi * 2
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Малювання оверлею через QPainter."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2

        if self._state == OverlayState.RECORDING:
            self._draw_recording(painter, center_x, center_y)
        elif self._state == OverlayState.PROCESSING:
            self._draw_processing(painter, center_x, center_y)
        elif self._state == OverlayState.SUCCESS:
            self._draw_success(painter, center_x, center_y)
        elif self._state == OverlayState.ERROR:
            self._draw_error(painter, center_x, center_y)

        painter.end()

    def _draw_recording(self, painter: QPainter, cx: float, cy: float) -> None:
        """Малює стан запису -- пульсуюче коло з градієнтом."""
        # Розмір кола залежить від амплітуди
        pulse = math.sin(self._pulse_phase) * 0.1
        amp_factor = 1.0 + self._amplitude * 0.4 + pulse
        radius = self._base_radius * amp_factor

        # Зовнішнє свічення
        glow_radius = radius * 1.5
        glow_gradient = QRadialGradient(cx, cy, glow_radius)
        glow_color = QColor(124, 110, 240)
        glow_color.setAlphaF(0.15 * self._opacity)
        glow_gradient.setColorAt(0.0, glow_color)
        glow_color.setAlphaF(0.0)
        glow_gradient.setColorAt(1.0, glow_color)
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QRectF(cx - glow_radius, cy - glow_radius, glow_radius * 2, glow_radius * 2)
        )

        # Основне коло з градієнтом синій-фіолетовий
        gradient = QRadialGradient(cx, cy, radius)
        color1 = QColor(100, 100, 255)
        color1.setAlphaF(0.7 * self._opacity)
        color2 = QColor(160, 80, 240)
        color2.setAlphaF(0.5 * self._opacity)
        gradient.setColorAt(0.0, color1)
        gradient.setColorAt(1.0, color2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Внутрішнє ядро (яскравіше)
        inner_radius = radius * 0.4
        inner_gradient = QRadialGradient(cx, cy, inner_radius)
        inner_color = QColor(180, 160, 255)
        inner_color.setAlphaF(0.6 * self._opacity)
        inner_gradient.setColorAt(0.0, inner_color)
        inner_color.setAlphaF(0.0)
        inner_gradient.setColorAt(1.0, inner_color)
        painter.setBrush(QBrush(inner_gradient))
        painter.drawEllipse(
            QRectF(cx - inner_radius, cy - inner_radius, inner_radius * 2, inner_radius * 2)
        )

        # Текст
        if self._show_text:
            font = QFont("Segoe UI", 12)
            painter.setFont(font)
            text_color = QColor(255, 255, 255)
            text_color.setAlphaF(0.9 * self._opacity)
            painter.setPen(QPen(text_color))
            text_y = cy + radius + 30
            painter.drawText(
                QRectF(0, text_y, self.width(), 30),
                Qt.AlignmentFlag.AlignCenter,
                "Говорiть...",
            )

    def _draw_processing(self, painter: QPainter, cx: float, cy: float) -> None:
        """Малює стан обробки -- помаранчеве коло з анімацією."""
        radius = self._base_radius * 0.9

        # Основне коло
        gradient = QRadialGradient(cx, cy, radius)
        color1 = QColor(255, 152, 0)
        color1.setAlphaF(0.7 * self._opacity)
        color2 = QColor(255, 87, 34)
        color2.setAlphaF(0.5 * self._opacity)
        gradient.setColorAt(0.0, color1)
        gradient.setColorAt(1.0, color2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Анімовані крапки
        dots_y = cy
        dot_radius = 5
        spacing = 20
        num_dots = 3
        start_x = cx - (num_dots - 1) * spacing / 2

        for i in range(num_dots):
            phase = self._pulse_phase + i * 0.8
            offset_y = math.sin(phase) * 10
            dot_color = QColor(255, 255, 255)
            dot_color.setAlphaF(0.8 * self._opacity)
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(
                QRectF(
                    start_x + i * spacing - dot_radius,
                    dots_y + offset_y - dot_radius,
                    dot_radius * 2,
                    dot_radius * 2,
                )
            )

        # Текст
        if self._show_text:
            font = QFont("Segoe UI", 12)
            painter.setFont(font)
            text_color = QColor(255, 255, 255)
            text_color.setAlphaF(0.9 * self._opacity)
            painter.setPen(QPen(text_color))
            text_y = cy + radius + 30
            painter.drawText(
                QRectF(0, text_y, self.width(), 30),
                Qt.AlignmentFlag.AlignCenter,
                "Розпiзнавання...",
            )

    def _draw_success(self, painter: QPainter, cx: float, cy: float) -> None:
        """Малює стан успіху -- зелене коло з галочкою."""
        radius = self._base_radius * 0.8

        # Зелене коло
        gradient = QRadialGradient(cx, cy, radius)
        color1 = QColor(76, 175, 80)
        color1.setAlphaF(0.7 * self._opacity)
        color2 = QColor(56, 142, 60)
        color2.setAlphaF(0.5 * self._opacity)
        gradient.setColorAt(0.0, color1)
        gradient.setColorAt(1.0, color2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Галочка
        check_color = QColor(255, 255, 255)
        check_color.setAlphaF(0.9 * self._opacity)
        pen = QPen(check_color, 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        size = radius * 0.4
        painter.drawLine(
            int(cx - size * 0.5),
            int(cy),
            int(cx - size * 0.1),
            int(cy + size * 0.4),
        )
        painter.drawLine(
            int(cx - size * 0.1),
            int(cy + size * 0.4),
            int(cx + size * 0.5),
            int(cy - size * 0.3),
        )

        # Текст результату
        if self._show_text and self._result_text:
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            text_color = QColor(255, 255, 255)
            text_color.setAlphaF(0.8 * self._opacity)
            painter.setPen(QPen(text_color))
            text_y = cy + radius + 25
            painter.drawText(
                QRectF(10, text_y, self.width() - 20, 40),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._result_text,
            )

    def _draw_error(self, painter: QPainter, cx: float, cy: float) -> None:
        """Малює стан помилки -- червоне коло з хрестиком."""
        radius = self._base_radius * 0.8

        # Червоне коло
        gradient = QRadialGradient(cx, cy, radius)
        color1 = QColor(244, 67, 54)
        color1.setAlphaF(0.7 * self._opacity)
        color2 = QColor(211, 47, 47)
        color2.setAlphaF(0.5 * self._opacity)
        gradient.setColorAt(0.0, color1)
        gradient.setColorAt(1.0, color2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Хрестик
        cross_color = QColor(255, 255, 255)
        cross_color.setAlphaF(0.9 * self._opacity)
        pen = QPen(cross_color, 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        size = radius * 0.3
        painter.drawLine(int(cx - size), int(cy - size), int(cx + size), int(cy + size))
        painter.drawLine(int(cx + size), int(cy - size), int(cx - size), int(cy + size))

        # Текст помилки
        if self._show_text and self._error_text:
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            text_color = QColor(255, 255, 255)
            text_color.setAlphaF(0.8 * self._opacity)
            painter.setPen(QPen(text_color))
            text_y = cy + radius + 25
            painter.drawText(
                QRectF(10, text_y, self.width() - 20, 30),
                Qt.AlignmentFlag.AlignCenter,
                self._error_text,
            )
