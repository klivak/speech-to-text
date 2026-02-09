"""Точка входу додатку EchoScribe."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

_MUTEX_NAME = "EchoScribe_SingleInstance"


def _kill_existing() -> None:
    """Завершує iснуючий процес EchoScribe."""
    import subprocess

    # Шукаємо процеси python з src.main або EchoScribe
    current_pid = os.getpid()
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name like '%python%'", "get", "processid,commandline"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            if "src.main" in line or "src\\main" in line or "EchoScribe" in line:
                parts = line.strip().split()
                if parts:
                    try:
                        pid = int(parts[-1])
                        if pid != current_pid:
                            os.kill(pid, 9)
                    except (ValueError, OSError):
                        pass
    except Exception:
        pass


def main() -> None:
    """Запуск додатку EchoScribe."""
    import ctypes

    # Перевiрка на єдиний екземпляр через Windows Named Mutex
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    mutex = kernel32.CreateMutexW(None, True, _MUTEX_NAME)
    last_error = kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        # Вже є запущений екземпляр -- завершуємо його та запускаємо новий
        kernel32.CloseHandle(mutex)
        _kill_existing()
        # Повторно створюємо mutex
        import time

        time.sleep(1)
        mutex = kernel32.CreateMutexW(None, True, _MUTEX_NAME)

    # Встановлюємо AppUserModelID для коректного відображення назви в Windows
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("EchoScribe")  # type: ignore[attr-defined]

    # Завантажуємо змінні оточення
    load_dotenv()

    # Налаштовуємо логування
    from src.utils.log_filter import setup_logging

    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_file = os.environ.get("LOG_FILE") or None
    setup_logging(level=log_level, log_file=log_file)

    import logging

    logger = logging.getLogger(__name__)
    logger.info("Запуск EchoScribe...")

    # Перевіряємо PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("[ПОМИЛКА] PyQt6 не встановлено. Запустiть: pip install PyQt6")
        sys.exit(1)

    # Створюємо QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("EchoScribe")
    app.setQuitOnLastWindowClosed(False)  # Залишаємо працювати в треї

    # Запускаємо головний клас
    from src.app import EchoScribeApp

    voice_app = EchoScribeApp(app)  # noqa: F841  -- prevent GC

    logger.info("EchoScribe готовий до роботи.")

    # Запускаємо event loop
    exit_code = app.exec()

    # Звiльняємо mutex
    kernel32.ReleaseMutex(mutex)
    kernel32.CloseHandle(mutex)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
