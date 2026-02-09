"""Безпечне зберігання та отримання API ключа OpenAI."""

from __future__ import annotations

import logging
import os

import keyring
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class SecureKeyManager:
    """Безпечне зберігання та отримання API ключа.

    Пріоритет джерел:
    1. Змінна оточення OPENAI_API_KEY
    2. Windows Credential Manager (через keyring)
    3. .env файл

    Ключ НІКОЛИ не зберігається в config.json або в коді.
    """

    APP_NAME = "EchoScribe"
    KEY_NAME = "openai_api_key"

    @staticmethod
    def get_key() -> str | None:
        """Отримує API ключ з доступних джерел."""
        # 1. Змінна оточення (найвищий пріоритет)
        key = os.environ.get("OPENAI_API_KEY")
        if key:
            logger.debug("API ключ отримано зі змінної оточення.")
            return key

        # 2. Windows Credential Manager
        try:
            key = keyring.get_password(SecureKeyManager.APP_NAME, SecureKeyManager.KEY_NAME)
            if key:
                logger.info(
                    "API ключ отримано з Windows Credential Manager (довжина: %d).", len(key)
                )
                return key
            else:
                logger.info("API ключ НЕ знайдено в Windows Credential Manager.")
        except Exception as e:
            logger.warning("Windows Credential Manager недоступний: %s", e)

        # 3. .env файл
        load_dotenv()
        key = os.environ.get("OPENAI_API_KEY")
        if key:
            logger.debug("API ключ отримано з .env файлу.")
            return key

        return None

    @staticmethod
    def save_key(key: str) -> bool:
        """Зберігає API ключ в Windows Credential Manager.

        Повертає True якщо збереження успішне.
        """
        try:
            keyring.set_password(SecureKeyManager.APP_NAME, SecureKeyManager.KEY_NAME, key)
            logger.info("API ключ збережено в Windows Credential Manager (довжина: %d).", len(key))
            # Перевіряємо що ключ справді зберігся
            check = keyring.get_password(SecureKeyManager.APP_NAME, SecureKeyManager.KEY_NAME)
            if check:
                logger.info("Верифікація збереження: ключ присутній (довжина: %d).", len(check))
            else:
                logger.error("Верифікація збереження: ключ НЕ знайдено після збереження!")
            return True
        except Exception as e:
            logger.error("Не вдалося зберегти API ключ: %s", e)
            return False

    @staticmethod
    def delete_key() -> bool:
        """Видаляє API ключ з Windows Credential Manager.

        Повертає True якщо видалення успішне.
        """
        try:
            keyring.delete_password(SecureKeyManager.APP_NAME, SecureKeyManager.KEY_NAME)
            logger.info("API ключ видалено з Windows Credential Manager.")
            return True
        except Exception as e:
            logger.debug("Не вдалося видалити API ключ: %s", e)
            return False

    @staticmethod
    def is_configured() -> bool:
        """Перевіряє чи налаштовано API ключ."""
        return SecureKeyManager.get_key() is not None

    @staticmethod
    def validate_key_format(key: str) -> bool:
        """Базова валідація формату API ключа."""
        if not key:
            return False
        return key.startswith("sk-") and len(key) > 20
