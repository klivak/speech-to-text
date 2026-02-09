"""Візуальний оверлей при записі -- пульсуюче коло з візуалізацією амплітуди."""

from __future__ import annotations

import math
import time
from enum import Enum, auto

from PyQt6.QtCore import QPoint, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QPainter,
    QPaintEvent,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QApplication, QWidget

from src.constants import OVERLAY_SIZES


class OverlayState(Enum):
    """Стани оверлею."""

    HIDDEN = auto()
    LOADING = auto()
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
        self._smooth_amplitude = 0.0
        self._pulse_phase = 0.0
        self._result_text = ""
        self._error_text = ""
        self._processing_start = 0.0
        self._recording_duration = 0.0
        self._recording_start = 0.0
        self._loading_text = ""
        self._loading_progress = 0.0
        self._loading_start = 0.0

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

    def show_loading(self, text: str = "Завантаження моделi...") -> None:
        """Показує оверлей в стані завантаження моделі."""
        self._state = OverlayState.LOADING
        self._loading_text = text
        self._loading_progress = 0.0
        self._loading_start = time.time()
        self._pulse_phase = 0.0
        self._position_on_screen()
        self.show()
        self._anim_timer.start()

    def set_loading_progress(self, progress: float, text: str | None = None) -> None:
        """Оновлює прогрес завантаження (0.0 - 1.0)."""
        self._loading_progress = max(0.0, min(1.0, progress))
        if text is not None:
            self._loading_text = text

    def hide_loading(self) -> None:
        """Ховає оверлей завантаження."""
        if self._state == OverlayState.LOADING:
            self.hide_overlay()

    def show_recording(self) -> None:
        """Показує оверлей в стані запису."""
        self._state = OverlayState.RECORDING
        self._amplitude = 0.0
        self._smooth_amplitude = 0.0
        self._pulse_phase = 0.0
        self._recording_start = time.time()
        self._position_on_screen()
        self.show()
        self._anim_timer.start()

    def show_processing(self) -> None:
        """Перемикає оверлей в стан обробки."""
        self._recording_duration = time.time() - self._recording_start
        self._processing_start = time.time()
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
        """Крок анімації з плавною інтерполяцією."""
        self._pulse_phase += 0.03
        if self._pulse_phase > math.pi * 2:
            self._pulse_phase -= math.pi * 2

        # Плавна інтерполяція амплітуди (lerp)
        lerp_speed = 0.12
        self._smooth_amplitude += (self._amplitude - self._smooth_amplitude) * lerp_speed

        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Малювання оверлею через QPainter."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2

        if self._state == OverlayState.LOADING:
            self._draw_loading(painter, center_x, center_y)
        elif self._state == OverlayState.RECORDING:
            self._draw_recording(painter, center_x, center_y)
        elif self._state == OverlayState.PROCESSING:
            self._draw_processing(painter, center_x, center_y)
        elif self._state == OverlayState.SUCCESS:
            self._draw_success(painter, center_x, center_y)
        elif self._state == OverlayState.ERROR:
            self._draw_error(painter, center_x, center_y)

        painter.end()

    def _draw_loading(self, painter: QPainter, cx: float, cy: float) -> None:
        """Малює стан завантаження моделі -- пульсуюче коло з прогрес-баром."""
        radius = self._base_radius * 0.85
        elapsed = time.time() - self._loading_start
        progress = self._loading_progress

        # 1. Зовнішнє свічення (синьо-фіолетове, повільне пульсування)
        pulse = 0.08 + math.sin(self._pulse_phase) * 0.04
        glow_r = radius * 1.6
        glow_grad = QRadialGradient(cx, cy, glow_r)
        gc = QColor(80, 120, 255)
        gc.setAlphaF(pulse * self._opacity)
        glow_grad.setColorAt(0.3, gc)
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

        # 2. Основне коло (темне, напівпрозоре)
        gradient = QRadialGradient(cx - radius * 0.2, cy - radius * 0.2, radius * 1.1)
        c1 = QColor(40, 60, 120)
        c1.setAlphaF(0.65 * self._opacity)
        c2 = QColor(25, 30, 80)
        c2.setAlphaF(0.55 * self._opacity)
        gradient.setColorAt(0.0, c1)
        gradient.setColorAt(1.0, c2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # 3. Обертове кільце (повільне, синє)
        ring_radius = radius * 1.12
        ring_width = 3.0
        angle_deg = math.degrees(self._pulse_phase * 1.5) % 360
        conical = QConicalGradient(cx, cy, angle_deg)
        c_blue = QColor(80, 160, 255)
        c_blue.setAlphaF(0.7 * self._opacity)
        c_purple = QColor(120, 60, 220)
        c_purple.setAlphaF(0.5 * self._opacity)
        c_fade = QColor(80, 160, 255)
        c_fade.setAlphaF(0.0)
        conical.setColorAt(0.0, c_blue)
        conical.setColorAt(0.3, c_purple)
        conical.setColorAt(0.6, c_blue)
        conical.setColorAt(0.9, c_fade)
        conical.setColorAt(1.0, c_blue)
        pen = QPen(QBrush(conical), ring_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            QRectF(cx - ring_radius, cy - ring_radius, ring_radius * 2, ring_radius * 2)
        )

        # 4. Прогрес-бар (горизонтальний, всередині кола)
        bar_width = radius * 1.2
        bar_height = 8.0
        bar_x = cx - bar_width / 2
        bar_y = cy + 8

        # Фон бару
        bg_color = QColor(20, 25, 50)
        bg_color.setAlphaF(0.6 * self._opacity)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            QRectF(bar_x, bar_y, bar_width, bar_height), bar_height / 2, bar_height / 2
        )

        # Заповнення бару
        if progress > 0.01:
            fill_width = bar_width * progress
            fill_grad = QRadialGradient(bar_x + fill_width, bar_y + bar_height / 2, fill_width)
            fc1 = QColor(80, 180, 255)
            fc1.setAlphaF(0.9 * self._opacity)
            fc2 = QColor(120, 80, 240)
            fc2.setAlphaF(0.8 * self._opacity)
            fill_grad.setColorAt(0.0, fc1)
            fill_grad.setColorAt(1.0, fc2)
            painter.setBrush(QBrush(fill_grad))
            painter.drawRoundedRect(
                QRectF(bar_x, bar_y, fill_width, bar_height), bar_height / 2, bar_height / 2
            )
        else:
            # Невизначений прогрес -- біжуча смужка
            stripe_width = bar_width * 0.3
            stripe_phase = (elapsed * 0.8) % 1.0
            stripe_x = bar_x + (bar_width - stripe_width) * stripe_phase
            sc = QColor(80, 180, 255)
            sc.setAlphaF(0.7 * self._opacity)
            painter.setBrush(QBrush(sc))
            painter.drawRoundedRect(
                QRectF(stripe_x, bar_y, stripe_width, bar_height),
                bar_height / 2,
                bar_height / 2,
            )

        # 5. Іконка завантаження (стрілка вниз) над прогрес-баром
        arrow_size = radius * 0.2
        arrow_y = cy - radius * 0.15
        arrow_color = QColor(160, 210, 255)
        arrow_color.setAlphaF(0.85 * self._opacity)
        arrow_pen = QPen(arrow_color, 3)
        arrow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        arrow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(arrow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Вертикальна лінія
        painter.drawLine(int(cx), int(arrow_y - arrow_size), int(cx), int(arrow_y + arrow_size))
        # Стрілка
        painter.drawLine(
            int(cx - arrow_size * 0.6),
            int(arrow_y + arrow_size * 0.4),
            int(cx),
            int(arrow_y + arrow_size),
        )
        painter.drawLine(
            int(cx + arrow_size * 0.6),
            int(arrow_y + arrow_size * 0.4),
            int(cx),
            int(arrow_y + arrow_size),
        )

        # 6. Відсоток
        if progress > 0.01:
            pct = int(progress * 100)
            font_pct = QFont("Segoe UI", 11)
            painter.setFont(font_pct)
            pct_color = QColor(180, 220, 255)
            pct_color.setAlphaF(0.85 * self._opacity)
            painter.setPen(QPen(pct_color))
            painter.drawText(
                QRectF(cx - 30, bar_y + bar_height + 4, 60, 20),
                Qt.AlignmentFlag.AlignCenter,
                f"{pct}%",
            )

        # 7. Текст знизу
        font = QFont("Segoe UI", 11)
        painter.setFont(font)
        text_color = QColor(160, 200, 255)
        text_color.setAlphaF(0.85 * self._opacity)
        painter.setPen(QPen(text_color))
        elapsed_sec = int(elapsed)
        text_y = cy + radius * 1.12 + 30
        time_str = f" ({elapsed_sec} сек)" if elapsed_sec > 2 else ""
        painter.drawText(
            QRectF(0, text_y, self.width(), 30),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._loading_text}{time_str}",
        )

    def _draw_recording(self, painter: QPainter, cx: float, cy: float) -> None:
        """Малює стан запису -- футуристичне коло з градієнтами та свіченням."""
        # Розмір кола залежить від амплітуди (smooth)
        amp = self._smooth_amplitude
        pulse = math.sin(self._pulse_phase) * 0.1
        amp_factor = 1.0 + amp * 0.4 + pulse
        radius = self._base_radius * amp_factor

        # 1. Зовнішнє неонове свічення (подвійний шар)
        for glow_mult, glow_alpha in [(2.0, 0.08), (1.6, 0.15)]:
            glow_r = radius * glow_mult
            glow_grad = QRadialGradient(cx, cy, glow_r)
            c = QColor(100, 180, 255)
            c.setAlphaF(glow_alpha * self._opacity)
            glow_grad.setColorAt(0.3, c)
            c2 = QColor(140, 80, 255)
            c2.setAlphaF(glow_alpha * 0.5 * self._opacity)
            glow_grad.setColorAt(0.6, c2)
            glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

        # 2. Обертове кільце (conical gradient)
        ring_radius = radius * 1.15
        ring_width = 3.0 + amp * 2.0
        angle_deg = math.degrees(self._pulse_phase * 3) % 360
        conical = QConicalGradient(cx, cy, angle_deg)
        c_cyan = QColor(0, 220, 255)
        c_cyan.setAlphaF(0.9 * self._opacity)
        c_purple = QColor(160, 60, 255)
        c_purple.setAlphaF(0.7 * self._opacity)
        c_trans = QColor(0, 220, 255)
        c_trans.setAlphaF(0.0)
        conical.setColorAt(0.0, c_cyan)
        conical.setColorAt(0.35, c_purple)
        conical.setColorAt(0.7, c_cyan)
        conical.setColorAt(0.95, c_trans)
        conical.setColorAt(1.0, c_cyan)
        pen = QPen(QBrush(conical), ring_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            QRectF(cx - ring_radius, cy - ring_radius, ring_radius * 2, ring_radius * 2)
        )

        # 3. Основне коло з багатошаровим радіальним градієнтом
        gradient = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 1.2)
        c_core = QColor(60, 180, 255)
        c_core.setAlphaF(0.75 * self._opacity)
        c_mid = QColor(120, 80, 240)
        c_mid.setAlphaF(0.6 * self._opacity)
        c_edge = QColor(80, 20, 180)
        c_edge.setAlphaF(0.45 * self._opacity)
        gradient.setColorAt(0.0, c_core)
        gradient.setColorAt(0.5, c_mid)
        gradient.setColorAt(1.0, c_edge)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # 4. Внутрішній блік (скляний ефект)
        highlight_r = radius * 0.55
        highlight_grad = QRadialGradient(cx - radius * 0.15, cy - radius * 0.25, highlight_r)
        h_color = QColor(200, 230, 255)
        h_color.setAlphaF(0.35 * self._opacity)
        highlight_grad.setColorAt(0.0, h_color)
        highlight_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(highlight_grad))
        painter.drawEllipse(
            QRectF(
                cx - highlight_r,
                cy - highlight_r - radius * 0.15,
                highlight_r * 2,
                highlight_r * 1.5,
            )
        )

        # 5. Яскраве ядро в центрі
        core_r = radius * 0.2 + amp * radius * 0.15
        core_grad = QRadialGradient(cx, cy, core_r)
        cc = QColor(180, 230, 255)
        cc.setAlphaF(0.7 * self._opacity)
        core_grad.setColorAt(0.0, cc)
        core_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(QRectF(cx - core_r, cy - core_r, core_r * 2, core_r * 2))

        # 6. Амплітудні часточки навколо кола
        num_particles = 12
        for i in range(num_particles):
            angle = (2 * math.pi / num_particles) * i + self._pulse_phase * 2
            dist = radius * (1.05 + amp * 0.3 + math.sin(angle * 3 + self._pulse_phase) * 0.08)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            p_size = 2.0 + amp * 3.0
            p_color = QColor(100, 220, 255)
            p_color.setAlphaF((0.4 + amp * 0.5) * self._opacity)
            painter.setBrush(QBrush(p_color))
            painter.drawEllipse(QRectF(px - p_size / 2, py - p_size / 2, p_size, p_size))

        # Текст
        if self._show_text:
            font = QFont("Segoe UI", 12)
            painter.setFont(font)
            text_color = QColor(180, 230, 255)
            text_color.setAlphaF(0.9 * self._opacity)
            painter.setPen(QPen(text_color))
            text_y = cy + radius * 1.15 + 35
            painter.drawText(
                QRectF(0, text_y, self.width(), 30),
                Qt.AlignmentFlag.AlignCenter,
                "Говорiть...",
            )

    def _draw_processing(self, painter: QPainter, cx: float, cy: float) -> None:
        """Малює стан обробки -- футуристичне коло з прогресом."""
        radius = self._base_radius * 0.9
        elapsed = time.time() - self._processing_start

        # Приблизний прогрес: оцінка ~2x тривалості запису для CPU
        estimated_time = max(self._recording_duration * 2.5, 3.0)
        progress = min(elapsed / estimated_time, 0.95)
        # Ease-out для реалістичності (сповільнюється до кінця)
        smooth_progress = 1.0 - (1.0 - progress) ** 2

        # 1. Зовнішнє свічення (amber/orange)
        glow_r = radius * 1.6
        glow_grad = QRadialGradient(cx, cy, glow_r)
        gc = QColor(255, 160, 0)
        gc.setAlphaF(0.12 * self._opacity)
        glow_grad.setColorAt(0.3, gc)
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

        # 2. Основне коло з градієнтом
        gradient = QRadialGradient(cx - radius * 0.2, cy - radius * 0.2, radius * 1.1)
        c1 = QColor(255, 180, 50)
        c1.setAlphaF(0.7 * self._opacity)
        c2 = QColor(220, 80, 20)
        c2.setAlphaF(0.5 * self._opacity)
        c3 = QColor(160, 40, 10)
        c3.setAlphaF(0.4 * self._opacity)
        gradient.setColorAt(0.0, c1)
        gradient.setColorAt(0.5, c2)
        gradient.setColorAt(1.0, c3)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # 3. Обертове кільце прогресу (conical gradient)
        ring_radius = radius * 1.12
        ring_width = 4.0
        angle_deg = math.degrees(self._pulse_phase * 2) % 360
        conical = QConicalGradient(cx, cy, angle_deg)
        c_amber = QColor(255, 200, 50)
        c_amber.setAlphaF(0.9 * self._opacity)
        c_red = QColor(255, 80, 30)
        c_red.setAlphaF(0.6 * self._opacity)
        c_fade = QColor(255, 200, 50)
        c_fade.setAlphaF(0.0)
        conical.setColorAt(0.0, c_amber)
        conical.setColorAt(0.3, c_red)
        conical.setColorAt(0.6, c_amber)
        conical.setColorAt(0.9, c_fade)
        conical.setColorAt(1.0, c_amber)
        pen = QPen(QBrush(conical), ring_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            QRectF(cx - ring_radius, cy - ring_radius, ring_radius * 2, ring_radius * 2)
        )

        # 4. Дуга прогресу (статична, показує %)
        progress_radius = radius * 0.65
        progress_width = 6.0
        progress_color = QColor(255, 240, 180)
        progress_color.setAlphaF(0.85 * self._opacity)
        progress_pen = QPen(progress_color, progress_width)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        start_angle = 90 * 16  # починаємо зверху
        span_angle = int(-smooth_progress * 360 * 16)
        painter.drawArc(
            QRectF(
                cx - progress_radius,
                cy - progress_radius,
                progress_radius * 2,
                progress_radius * 2,
            ),
            start_angle,
            span_angle,
        )

        # 5. Скляний блік
        highlight_r = radius * 0.45
        highlight_grad = QRadialGradient(cx - radius * 0.1, cy - radius * 0.2, highlight_r)
        h_color = QColor(255, 230, 200)
        h_color.setAlphaF(0.25 * self._opacity)
        highlight_grad.setColorAt(0.0, h_color)
        highlight_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(highlight_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QRectF(
                cx - highlight_r,
                cy - highlight_r - radius * 0.1,
                highlight_r * 2,
                highlight_r * 1.4,
            )
        )

        # 6. Відсоток в центрі
        pct = int(smooth_progress * 100)
        font_pct = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(font_pct)
        pct_color = QColor(255, 255, 255)
        pct_color.setAlphaF(0.9 * self._opacity)
        painter.setPen(QPen(pct_color))
        painter.drawText(
            QRectF(cx - 40, cy - 15, 80, 30),
            Qt.AlignmentFlag.AlignCenter,
            f"{pct}%",
        )

        # 7. Текст знизу
        if self._show_text:
            font = QFont("Segoe UI", 11)
            painter.setFont(font)
            text_color = QColor(255, 220, 160)
            text_color.setAlphaF(0.85 * self._opacity)
            painter.setPen(QPen(text_color))
            elapsed_sec = int(elapsed)
            text_y = cy + radius * 1.12 + 30
            painter.drawText(
                QRectF(0, text_y, self.width(), 30),
                Qt.AlignmentFlag.AlignCenter,
                f"Розпiзнавання... {elapsed_sec} сек",
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
