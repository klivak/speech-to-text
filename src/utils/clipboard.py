"""Робота з буфером обміну та вставка тексту в активне вікно."""

from __future__ import annotations

import logging
import time

import pyautogui
import pyperclip

logger = logging.getLogger(__name__)


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

        # Невелика пауза для надійності
        time.sleep(0.05)

        # Вставляємо через Ctrl+V
        pyautogui.hotkey("ctrl", "v")

        # Пауза перед відновленням буфера
        time.sleep(0.1)

        # Відновлюємо попередній вміст буфера
        try:
            pyperclip.copy(original_clipboard)
        except Exception as e:
            logger.warning("Не вдалось відновити буфер обміну: %s", e)

        logger.debug("Текст вставлено: %d символів.", len(text))
        return True

    except Exception as e:
        logger.error("Помилка вставки тексту: %s", e)
        return False
