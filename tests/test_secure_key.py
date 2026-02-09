"""Тести для SecureKeyManager."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from src.utils.secure_key import SecureKeyManager


class TestSecureKeyManager:
    """Тести менеджера безпечного зберігання ключів."""

    def test_validate_key_format_valid(self) -> None:
        """Валідний формат ключа."""
        assert SecureKeyManager.validate_key_format("sk-1234567890abcdefghijklmnop")
        assert SecureKeyManager.validate_key_format("sk-proj-abcdefghijklmnopqrstuvwxyz")

    def test_validate_key_format_invalid(self) -> None:
        """Невалідний формат ключа."""
        assert not SecureKeyManager.validate_key_format("")
        assert not SecureKeyManager.validate_key_format("invalid-key")
        assert not SecureKeyManager.validate_key_format("sk-short")

    def test_get_key_from_env(self) -> None:
        """Отримує ключ зі змінної оточення."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test1234567890abcdefg"}):
            key = SecureKeyManager.get_key()
            assert key == "sk-test1234567890abcdefg"

    def test_get_key_none_when_not_configured(self) -> None:
        """Повертає None якщо ключ не налаштовано."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("src.utils.secure_key.keyring") as mock_kr:
                mock_kr.get_password.return_value = None
                with patch("src.utils.secure_key.load_dotenv"):
                    key = SecureKeyManager.get_key()
                    assert key is None

    def test_is_configured_true(self) -> None:
        """is_configured повертає True коли ключ є."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test1234567890abcdefg"}):
            assert SecureKeyManager.is_configured()

    def test_is_configured_false(self) -> None:
        """is_configured повертає False коли ключа немає."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("src.utils.secure_key.keyring") as mock_kr:
                mock_kr.get_password.return_value = None
                with patch("src.utils.secure_key.load_dotenv"):
                    assert not SecureKeyManager.is_configured()
