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
        self._pulse_phase += 0.02
        if self._pulse_phase > math.pi * 200:
            self._pulse_phase -= math.pi * 200

        # Плавна інтерполяція амплітуди (exponential lerp для природнього руху)
        lerp_speed = 0.08
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
        """Малює стан завантаження -- футуристичний голографічний дизайн."""
        radius = self._base_radius * 0.85
        elapsed = time.time() - self._loading_start
        progress = self._loading_progress
        t = self._pulse_phase

        # Динамічні кольори
        hue = t * 0.1
        r_a = int(40 + 30 * math.sin(hue))
        g_a = int(100 + 60 * math.sin(hue * 0.7 + 1.0))
        b_a = int(220 + 35 * math.sin(hue * 0.5 + 2.0))

        # 1. Зовнішнє свічення -- пульсуюче, з переливами
        pulse = 0.08 + math.sin(t * 0.5) * 0.04 + math.sin(t * 0.8) * 0.02
        glow_r = radius * 2.0
        glow_grad = QRadialGradient(cx, cy, glow_r)
        gc = QColor(r_a, g_a, b_a)
        gc.setAlphaF(pulse * self._opacity)
        glow_grad.setColorAt(0.2, gc)
        gc2 = QColor(100, 40, 200)
        gc2.setAlphaF(pulse * 0.5 * self._opacity)
        glow_grad.setColorAt(0.5, gc2)
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

        # 2. Основне коло -- глибокий градієнт з рухомим центром
        gx = cx + math.sin(t * 0.3) * radius * 0.15
        gy = cy + math.cos(t * 0.25) * radius * 0.15
        gradient = QRadialGradient(gx, gy, radius * 1.1)
        c1 = QColor(30, 50, 110)
        c1.setAlphaF(0.7 * self._opacity)
        c2 = QColor(15, 20, 60)
        c2.setAlphaF(0.6 * self._opacity)
        gradient.setColorAt(0.0, c1)
        gradient.setColorAt(1.0, c2)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # 3. Подвійне обертове кільце -- два в протилежних напрямках
        for ring_i, (speed, width, alpha_mult) in enumerate([(1.0, 2.5, 0.7), (-0.6, 1.5, 0.4)]):
            ring_r = radius * (1.12 + ring_i * 0.08)
            angle = math.degrees(t * speed) % 360
            conical = QConicalGradient(cx, cy, angle)
            ca = QColor(r_a, g_a, b_a)
            ca.setAlphaF(alpha_mult * self._opacity)
            cb = QColor(160, 60, 240)
            cb.setAlphaF(alpha_mult * 0.6 * self._opacity)
            cf = QColor(r_a, g_a, b_a)
            cf.setAlphaF(0.0)
            conical.setColorAt(0.0, ca)
            conical.setColorAt(0.3, cb)
            conical.setColorAt(0.6, ca)
            conical.setColorAt(0.9, cf)
            conical.setColorAt(1.0, ca)
            pen = QPen(QBrush(conical), width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2))

        # 4. Орбітальні точки -- 3 точки що обертаються на різних орбітах
        for orb_i in range(3):
            orb_angle = t * (0.8 + orb_i * 0.3) + orb_i * (math.pi * 2 / 3)
            orb_r = radius * (0.7 + orb_i * 0.15)
            orb_x = cx + math.cos(orb_angle) * orb_r
            orb_y = cy + math.sin(orb_angle) * orb_r
            dot_size = 4.0 + math.sin(t + orb_i) * 1.5
            dot_color = QColor(
                int(120 + 80 * math.sin(hue + orb_i * 1.5)),
                int(180 + 60 * math.sin(hue * 0.7 + orb_i)),
                255,
            )
            dot_color.setAlphaF(0.8 * self._opacity)
            # Хвіст
            trail_grad = QRadialGradient(orb_x, orb_y, dot_size * 3)
            trail_c = QColor(dot_color)
            trail_c.setAlphaF(0.2 * self._opacity)
            trail_grad.setColorAt(0.0, trail_c)
            trail_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(trail_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QRectF(orb_x - dot_size * 3, orb_y - dot_size * 3, dot_size * 6, dot_size * 6)
            )
            # Точка
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(
                QRectF(orb_x - dot_size / 2, orb_y - dot_size / 2, dot_size, dot_size)
            )

        # 5. Кругова дуга прогресу (якщо є прогрес)
        if progress > 0.01:
            prog_r = radius * 0.55
            prog_width = 5.0
            prog_color = QColor(100, 200, 255)
            prog_color.setAlphaF(0.85 * self._opacity)
            prog_pen = QPen(prog_color, prog_width)
            prog_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(prog_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            start_angle = 90 * 16
            span_angle = int(-progress * 360 * 16)
            painter.drawArc(
                QRectF(cx - prog_r, cy - prog_r, prog_r * 2, prog_r * 2),
                start_angle,
                span_angle,
            )
            # Фонова дуга
            bg_color = QColor(40, 50, 80)
            bg_color.setAlphaF(0.3 * self._opacity)
            bg_pen = QPen(bg_color, prog_width)
            bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(bg_pen)
            painter.drawArc(
                QRectF(cx - prog_r, cy - prog_r, prog_r * 2, prog_r * 2),
                start_angle,
                -360 * 16,
            )
            # Перемалювання прогресу поверх
            painter.setPen(prog_pen)
            painter.drawArc(
                QRectF(cx - prog_r, cy - prog_r, prog_r * 2, prog_r * 2),
                start_angle,
                span_angle,
            )
        else:
            # Невизначений прогрес -- сканувальна дуга
            scan_r = radius * 0.55
            scan_width = 4.0
            scan_angle = (elapsed * 120) % 360
            scan_span = 90
            scan_color = QColor(80, 180, 255)
            scan_color.setAlphaF(0.6 * self._opacity)
            scan_pen = QPen(scan_color, scan_width)
            scan_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(scan_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(
                QRectF(cx - scan_r, cy - scan_r, scan_r * 2, scan_r * 2),
                int(scan_angle * 16),
                int(scan_span * 16),
            )

        # 6. Відсоток або іконка в центрі
        if progress > 0.01:
            pct = int(progress * 100)
            font_pct = QFont("Segoe UI", 18, QFont.Weight.Light)
            painter.setFont(font_pct)
            pct_color = QColor(180, 220, 255)
            pct_color.setAlphaF(0.9 * self._opacity)
            painter.setPen(QPen(pct_color))
            painter.drawText(
                QRectF(cx - 40, cy - 15, 80, 30),
                Qt.AlignmentFlag.AlignCenter,
                f"{pct}%",
            )
        else:
            # Стилізована іконка AI / мозок -- три з'єднані точки
            node_r = radius * 0.25
            nodes = [
                (cx, cy - node_r * 0.6),
                (cx - node_r * 0.5, cy + node_r * 0.4),
                (cx + node_r * 0.5, cy + node_r * 0.4),
            ]
            # З'єднання
            line_color = QColor(120, 180, 255)
            line_color.setAlphaF(0.5 * self._opacity)
            line_pen = QPen(line_color, 1.5)
            line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(line_pen)
            for i_n in range(len(nodes)):
                for j_n in range(i_n + 1, len(nodes)):
                    painter.drawLine(
                        int(nodes[i_n][0]),
                        int(nodes[i_n][1]),
                        int(nodes[j_n][0]),
                        int(nodes[j_n][1]),
                    )
            # Точки
            for nx, ny in nodes:
                nd_color = QColor(140, 200, 255)
                nd_color.setAlphaF(0.8 * self._opacity)
                painter.setBrush(QBrush(nd_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(nx - 3, ny - 3, 6, 6))

        # 7. Сканувальні лінії (горизонтальні, рухаються)
        scan_y = cy - radius * 0.7 + ((elapsed * 40) % (radius * 1.4))
        if abs(scan_y - cy) < radius * 0.95:
            # Ширина лінії залежить від відстані до центру
            dist_from_center = abs(scan_y - cy) / radius
            line_half_w = radius * math.sqrt(max(0, 1.0 - dist_from_center**2)) * 0.9
            scan_line_color = QColor(80, 160, 255)
            scan_line_color.setAlphaF(0.15 * self._opacity)
            scan_pen2 = QPen(scan_line_color, 1.0)
            painter.setPen(scan_pen2)
            painter.drawLine(
                int(cx - line_half_w),
                int(scan_y),
                int(cx + line_half_w),
                int(scan_y),
            )

        # 8. Скляний блік
        hl_r = radius * 0.5
        hl_grad = QRadialGradient(cx - radius * 0.1, cy - radius * 0.3, hl_r)
        hl_c = QColor(180, 220, 255)
        hl_c.setAlphaF(0.15 * self._opacity)
        hl_grad.setColorAt(0.0, hl_c)
        hl_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(hl_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - hl_r, cy - hl_r - radius * 0.15, hl_r * 2, hl_r * 1.3))

        # 9. Текст знизу
        font = QFont("Segoe UI", 11)
        painter.setFont(font)
        text_color = QColor(160, 200, 255)
        text_color.setAlphaF(0.85 * self._opacity)
        painter.setPen(QPen(text_color))
        elapsed_sec = int(elapsed)
        text_y = cy + radius * 1.2 + 30
        time_str = f" ({elapsed_sec} сек)" if elapsed_sec > 2 else ""
        painter.drawText(
            QRectF(0, text_y, self.width(), 30),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._loading_text}{time_str}",
        )

    def _draw_recording(self, painter: QPainter, cx: float, cy: float) -> None:
        """Малює стан запису -- плавні градієнти що переливаються різними кольорами."""
        amp = self._smooth_amplitude
        t = self._pulse_phase

        # Плавна пульсація (комбінація синусоїд для органічного руху)
        pulse = math.sin(t * 0.7) * 0.06 + math.sin(t * 1.3) * 0.04
        amp_factor = 1.0 + amp * 0.35 + pulse
        radius = self._base_radius * amp_factor

        # Динамічні кольори -- плавно змінюються з часом (завжди трохи різні)
        hue_shift = t * 0.15
        r1 = int(60 + 40 * math.sin(hue_shift))
        g1 = int(140 + 80 * math.sin(hue_shift * 0.7 + 1.0))
        b1 = int(220 + 35 * math.sin(hue_shift * 0.5 + 2.0))

        r2 = int(140 + 60 * math.sin(hue_shift * 0.6 + 3.0))
        g2 = int(60 + 40 * math.sin(hue_shift * 0.9 + 0.5))
        b2 = int(240 + 15 * math.sin(hue_shift * 0.4 + 1.5))

        r3 = int(200 + 55 * math.sin(hue_shift * 0.8 + 2.5))
        g3 = int(100 + 80 * math.sin(hue_shift * 0.5 + 4.0))
        b3 = int(180 + 60 * math.sin(hue_shift * 0.3 + 0.8))

        # 1. Зовнішнє свічення (подвійне, кольори з часом)
        for glow_mult, glow_alpha in [(2.2, 0.06), (1.7, 0.12)]:
            glow_r = radius * glow_mult
            glow_grad = QRadialGradient(cx, cy, glow_r)
            c = QColor(r1, g1, b1)
            c.setAlphaF(glow_alpha * (1.0 + amp * 0.5) * self._opacity)
            glow_grad.setColorAt(0.2, c)
            c2 = QColor(r2, g2, b2)
            c2.setAlphaF(glow_alpha * 0.4 * self._opacity)
            glow_grad.setColorAt(0.6, c2)
            glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

        # 2. Обертове кільце з градієнтом що переливається
        ring_radius = radius * 1.15
        ring_width = 2.5 + amp * 2.5
        angle_deg = math.degrees(t * 1.2) % 360
        conical = QConicalGradient(cx, cy, angle_deg)
        c_a = QColor(r1, g1, b1)
        c_a.setAlphaF(0.85 * self._opacity)
        c_b = QColor(r2, g2, b2)
        c_b.setAlphaF(0.65 * self._opacity)
        c_c = QColor(r3, g3, b3)
        c_c.setAlphaF(0.75 * self._opacity)
        c_fade = QColor(r1, g1, b1)
        c_fade.setAlphaF(0.0)
        conical.setColorAt(0.0, c_a)
        conical.setColorAt(0.25, c_b)
        conical.setColorAt(0.5, c_c)
        conical.setColorAt(0.75, c_a)
        conical.setColorAt(0.92, c_fade)
        conical.setColorAt(1.0, c_a)
        pen = QPen(QBrush(conical), ring_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            QRectF(cx - ring_radius, cy - ring_radius, ring_radius * 2, ring_radius * 2)
        )

        # 3. Основне коло з градієнтом що дихає
        grad_offset_x = math.sin(t * 0.5) * radius * 0.2
        grad_offset_y = math.cos(t * 0.4) * radius * 0.2
        gradient = QRadialGradient(cx + grad_offset_x, cy + grad_offset_y, radius * 1.2)
        c_core = QColor(r1, g1, b1)
        c_core.setAlphaF(0.7 * self._opacity)
        c_mid = QColor(r2, g2, b2)
        c_mid.setAlphaF(0.55 * self._opacity)
        c_edge = QColor(r3, g3, b3)
        c_edge.setAlphaF(0.4 * self._opacity)
        gradient.setColorAt(0.0, c_core)
        gradient.setColorAt(0.5, c_mid)
        gradient.setColorAt(1.0, c_edge)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # 4. Внутрішній блік (скляний ефект, рухається)
        highlight_r = radius * 0.5
        hl_x = cx + math.sin(t * 0.3) * radius * 0.1
        hl_y = cy - radius * 0.2 + math.cos(t * 0.25) * radius * 0.05
        highlight_grad = QRadialGradient(hl_x, hl_y, highlight_r)
        h_color = QColor(220, 240, 255)
        h_color.setAlphaF(0.3 * self._opacity)
        highlight_grad.setColorAt(0.0, h_color)
        highlight_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(highlight_grad))
        painter.drawEllipse(
            QRectF(hl_x - highlight_r, hl_y - highlight_r, highlight_r * 2, highlight_r * 1.4)
        )

        # 5. Яскраве ядро що пульсує
        core_pulse = 0.2 + amp * 0.15 + math.sin(t * 1.5) * 0.05
        core_r = radius * core_pulse
        core_grad = QRadialGradient(cx, cy, core_r)
        cc = QColor(r3, min(255, g3 + 80), min(255, b3 + 40))
        cc.setAlphaF(0.6 * self._opacity)
        core_grad.setColorAt(0.0, cc)
        core_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(QRectF(cx - core_r, cy - core_r, core_r * 2, core_r * 2))

        # 6. Частинки -- різних кольорів, плавно рухаються
        num_particles = 16
        for i in range(num_particles):
            angle = (2 * math.pi / num_particles) * i + t * 0.8
            wobble = math.sin(angle * 2.5 + t * 1.2) * 0.1
            dist = radius * (1.08 + amp * 0.25 + wobble)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            p_size = 1.5 + amp * 3.0 + math.sin(t + i * 0.7) * 1.0
            # Кожна частинка свого відтінку
            ph = (i / num_particles + t * 0.05) % 1.0
            p_r = int(80 + 120 * math.sin(ph * math.pi * 2))
            p_g = int(160 + 80 * math.sin(ph * math.pi * 2 + 2.0))
            p_b = int(200 + 55 * math.sin(ph * math.pi * 2 + 4.0))
            p_color = QColor(p_r, p_g, p_b)
            p_color.setAlphaF((0.3 + amp * 0.5) * self._opacity)
            painter.setBrush(QBrush(p_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(px - p_size / 2, py - p_size / 2, p_size, p_size))

        # Текст
        if self._show_text:
            elapsed = time.time() - self._recording_start
            font = QFont("Segoe UI", 12)
            painter.setFont(font)
            text_color = QColor(200, 230, 255)
            text_color.setAlphaF(0.85 * self._opacity)
            painter.setPen(QPen(text_color))
            text_y = cy + radius * 1.15 + 35
            elapsed_sec = int(elapsed)
            label = f"Говорiть... {elapsed_sec} сек" if elapsed_sec > 0 else "Говорiть..."
            painter.drawText(
                QRectF(0, text_y, self.width(), 30),
                Qt.AlignmentFlag.AlignCenter,
                label,
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
