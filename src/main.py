"""Точка входу додатку VoiceType."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv


def main() -> None:
    """Запуск додатку VoiceType."""
    # Завантажуємо змінні оточення
    load_dotenv()

    # Налаштовуємо логування
    from src.utils.log_filter import setup_logging

    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_file = os.environ.get("LOG_FILE") or None
    setup_logging(level=log_level, log_file=log_file)

    import logging

    logger = logging.getLogger(__name__)
    logger.info("Запуск VoiceType...")

    # Перевіряємо PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("[ПОМИЛКА] PyQt6 не встановлено. Запустiть: pip install PyQt6")
        sys.exit(1)

    # Створюємо QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("VoiceType")
    app.setQuitOnLastWindowClosed(False)  # Залишаємо працювати в треї

    # Запускаємо головний клас
    from src.app import VoiceTypeApp

    voice_app = VoiceTypeApp(app)  # noqa: F841  -- prevent GC

    logger.info("VoiceType готовий до роботи.")

    # Запускаємо event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
