"""Менеджер тем оформлення -- автодетект системної теми Windows та перемикання."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def get_windows_theme() -> str:
    """Визначає поточну тему Windows: 'dark' або 'light'."""
    try:
        import winreg

        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(
            registry,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except Exception:
        return "dark"


def _get_themes_dir() -> Path:
    """Повертає шлях до директорії з файлами тем."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS) / "src" / "ui" / "themes"  # type: ignore[attr-defined]
    else:
        base = Path(__file__).parent
    return base


def _get_assets_dir() -> Path:
    """Повертає шлях до директорії assets."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets"  # type: ignore[attr-defined]
    return Path(__file__).parent.parent.parent.parent / "assets"


def _load_qss(theme_name: str) -> str:
    """Завантажує QSS файл теми."""
    themes_dir = _get_themes_dir()
    qss_file = themes_dir / f"{theme_name}.qss"

    if not qss_file.exists():
        logger.warning("Файл теми не знайдено: %s", qss_file)
        return ""

    try:
        with open(qss_file, encoding="utf-8") as f:
            qss = f.read()
        # Замiна вiдносних шляхiв assets/ на абсолютнi
        assets_dir = _get_assets_dir()
        qss = qss.replace("url(assets/", f"url({assets_dir.as_posix()}/")
        return qss
    except OSError as e:
        logger.error("Помилка читання теми: %s", e)
        return ""


class ThemeManager:
    """Менеджер тем оформлення додатку.

    Підтримує три режими:
    - "system": автоматичне визначення теми Windows
    - "light": примусово світла тема
    - "dark": примусово темна тема
    """

    def __init__(self, app: QApplication, theme_preference: str = "system") -> None:
        self._app = app
        self._preference = theme_preference
        self._current_theme: str = ""

    @property
    def current_theme(self) -> str:
        """Поточна активна тема."""
        return self._current_theme

    @property
    def preference(self) -> str:
        """Налаштування теми користувача."""
        return self._preference

    def apply_theme(self, preference: str | None = None) -> None:
        """Застосовує тему згідно з налаштуваннями.

        Args:
            preference: "system", "light", або "dark". Якщо None -- використовує поточне.
        """
        if preference is not None:
            self._preference = preference

        theme = get_windows_theme() if self._preference == "system" else self._preference

        if theme == self._current_theme:
            return

        qss = _load_qss(theme)
        self._app.setStyleSheet(qss)
        self._current_theme = theme
        logger.info("Тему змінено на: %s", theme)

    def toggle_theme(self) -> str:
        """Перемикає між темною та світлою темою. Повертає нову тему."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.apply_theme(new_theme)
        return new_theme

    def get_colors(self) -> dict[str, str]:
        """Повертає кольори поточної теми для використання в QPainter."""
        if self._current_theme == "dark":
            return {
                "bg": "#1e1e2e",
                "surface": "#2a2a3d",
                "text": "#e0e0e0",
                "text_secondary": "#a0a0b0",
                "accent": "#7c6ef0",
                "success": "#4caf50",
                "error": "#f44336",
                "warning": "#ff9800",
                "border": "#3a3a4d",
            }
        else:
            return {
                "bg": "#ffffff",
                "surface": "#f5f5f5",
                "text": "#212121",
                "text_secondary": "#757575",
                "accent": "#6750a4",
                "success": "#4caf50",
                "error": "#f44336",
                "warning": "#ff9800",
                "border": "#e0e0e0",
            }
