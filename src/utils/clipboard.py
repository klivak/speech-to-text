"""Робота з буфером обміну та вставка тексту в активне вікно."""

from __future__ import annotations

import ctypes
import logging
import time

import keyboard
import pyperclip

logger = logging.getLogger(__name__)

# Win32 константи
_VK_CONTROL = 0x11
_VK_V = 0x56
_KEYEVENTF_KEYUP = 0x0002


def paste_text(text: str) -> bool:
    """Вставляє текст в активне вікно через буфер обміну.

    Зберігає попередній вміст буфера та відновлює його після вставки.
    Повертає True якщо вставка успішна.
    """
    if not text:
        logger.warning("Порожній текст для вставки.")
        return False

    try:
        # Зберігаємо поточний вміст буфера
        original_clipboard = ""
        try:
            original_clipboard = pyperclip.paste()
        except Exception as e:
            logger.warning("Не вдалось прочитати буфер обміну: %s", e)

        # Копіюємо новий текст в буфер
        pyperclip.copy(text)

        # Чекаємо щоб гарячі клавіші були відпущені
        for key in ("ctrl", "shift", "alt"):
            try:
                if keyboard.is_pressed(key):
                    start = time.time()
                    while keyboard.is_pressed(key) and (time.time() - start) < 1.0:
                        time.sleep(0.02)
            except Exception:
                pass

        # Пауза для надійності
        time.sleep(0.05)

        # Вставляємо через Ctrl+V використовуючи Win32 API
        _send_ctrl_v()

        # Пауза перед відновленням буфера
        time.sleep(0.2)

        # Відновлюємо попередній вміст буфера
        try:
            pyperclip.copy(original_clipboard)
        except Exception as e:
            logger.warning("Не вдалось відновити буфер обміну: %s", e)

        logger.info("Текст вставлено: %d символів.", len(text))
        return True

    except Exception as e:
        logger.error("Помилка вставки тексту: %s", e)
        return False


def _send_ctrl_v() -> None:
    """Емулює Ctrl+V через Win32 SendInput API."""
    user32 = ctypes.windll.user32
    user32.keybd_event(_VK_CONTROL, 0, 0, 0)
    user32.keybd_event(_VK_V, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(_VK_V, 0, _KEYEVENTF_KEYUP, 0)
    user32.keybd_event(_VK_CONTROL, 0, _KEYEVENTF_KEYUP, 0)
