"""Фільтр логів для маскування API ключів та чутливих даних."""

from __future__ import annotations

import logging
import re

# Патерни для API ключiв рiзних провайдерiв
_API_KEY_PATTERN = re.compile(r"(sk-|gsk_)[A-Za-z0-9_-]{20,}")


def mask_api_key(text: str) -> str:
    """Маскує API ключі у тексті, залишаючи лише останні 4 символи."""

    def _replace(match: re.Match) -> str:
        key = match.group(0)
        prefix = match.group(1)
        return f"{prefix}...{key[-4:]}"

    return _API_KEY_PATTERN.sub(_replace, text)


class SecretFilter(logging.Filter):
    """Фільтр логування що автоматично маскує API ключі."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_api_key(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: mask_api_key(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    mask_api_key(str(a)) if isinstance(a, str) else a for a in record.args
                )
        return True


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """Налаштовує логування з фільтром секретів."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Кореневий логер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Фільтр секретів на кореневому рівні
    secret_filter = SecretFilter()

    # Консольний обробник
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(secret_filter)
    root_logger.addHandler(console_handler)

    # Файловий обробник (опціонально)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(secret_filter)
        root_logger.addHandler(file_handler)
