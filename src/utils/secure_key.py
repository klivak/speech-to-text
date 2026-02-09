"""Безпечне зберігання та отримання API ключiв для рiзних провайдерiв."""

from __future__ import annotations

import logging
import os

import keyring
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Маппiнг провайдерiв на iмена ключiв та змiнних оточення
_PROVIDER_KEYS: dict[str, dict[str, str]] = {
    "openai": {
        "key_name": "openai_api_key",
        "env_var": "OPENAI_API_KEY",
    },
    "groq": {
        "key_name": "groq_api_key",
        "env_var": "GROQ_API_KEY",
    },
    "deepgram": {
        "key_name": "deepgram_api_key",
        "env_var": "DEEPGRAM_API_KEY",
    },
}


class SecureKeyManager:
    """Безпечне зберігання та отримання API ключiв.

    Пріоритет джерел:
    1. Змінна оточення (OPENAI_API_KEY / GROQ_API_KEY / DEEPGRAM_API_KEY)
    2. Windows Credential Manager (через keyring)
    3. .env файл

    Ключi НІКОЛИ не зберігаються в config.json або в коді.
    """

    APP_NAME = "EchoScribe"
    # Зворотна сумiснiсть
    KEY_NAME = "openai_api_key"

    @staticmethod
    def _resolve(provider: str) -> tuple[str, str]:
        """Повертає (key_name, env_var) для провайдера."""
        info = _PROVIDER_KEYS.get(provider, _PROVIDER_KEYS["openai"])
        return info["key_name"], info["env_var"]

    @staticmethod
    def get_key(provider: str = "openai") -> str | None:
        """Отримує API ключ з доступних джерел."""
        key_name, env_var = SecureKeyManager._resolve(provider)

        # 1. Змінна оточення (найвищий пріоритет)
        key = os.environ.get(env_var)
        if key:
            logger.debug("API ключ (%s) отримано зі змінної оточення.", provider)
            return key

        # 2. Windows Credential Manager
        try:
            key = keyring.get_password(SecureKeyManager.APP_NAME, key_name)
            if key:
                logger.info(
                    "API ключ (%s) отримано з Windows Credential Manager (довжина: %d).",
                    provider,
                    len(key),
                )
                return key
            else:
                logger.info("API ключ (%s) НЕ знайдено в Windows Credential Manager.", provider)
        except Exception as e:
            logger.warning("Windows Credential Manager недоступний: %s", e)

        # 3. .env файл
        load_dotenv()
        key = os.environ.get(env_var)
        if key:
            logger.debug("API ключ (%s) отримано з .env файлу.", provider)
            return key

        return None

    @staticmethod
    def save_key(key: str, provider: str = "openai") -> bool:
        """Зберігає API ключ в Windows Credential Manager.

        Повертає True якщо збереження успішне.
        """
        key_name, _ = SecureKeyManager._resolve(provider)
        try:
            keyring.set_password(SecureKeyManager.APP_NAME, key_name, key)
            logger.info(
                "API ключ (%s) збережено в Windows Credential Manager (довжина: %d).",
                provider,
                len(key),
            )
            # Перевіряємо що ключ справді зберігся
            check = keyring.get_password(SecureKeyManager.APP_NAME, key_name)
            if check:
                logger.info("Верифікація збереження: ключ присутній (довжина: %d).", len(check))
            else:
                logger.error("Верифікація збереження: ключ НЕ знайдено після збереження!")
            return True
        except Exception as e:
            logger.error("Не вдалося зберегти API ключ (%s): %s", provider, e)
            return False

    @staticmethod
    def delete_key(provider: str = "openai") -> bool:
        """Видаляє API ключ з Windows Credential Manager.

        Повертає True якщо видалення успішне.
        """
        key_name, _ = SecureKeyManager._resolve(provider)
        try:
            keyring.delete_password(SecureKeyManager.APP_NAME, key_name)
            logger.info("API ключ (%s) видалено з Windows Credential Manager.", provider)
            return True
        except Exception as e:
            logger.debug("Не вдалося видалити API ключ (%s): %s", provider, e)
            return False

    @staticmethod
    def is_configured(provider: str = "openai") -> bool:
        """Перевіряє чи налаштовано API ключ."""
        return SecureKeyManager.get_key(provider) is not None

    @staticmethod
    def validate_key_format(key: str, provider: str = "openai") -> bool:
        """Базова валідація формату API ключа."""
        if not key or len(key) < 10:
            return False
        if provider == "openai":
            return key.startswith("sk-") and len(key) > 20
        if provider == "groq":
            return key.startswith("gsk_") and len(key) > 20
        # Deepgram та iншi -- просто перевіряємо довжину
        return len(key) > 10
