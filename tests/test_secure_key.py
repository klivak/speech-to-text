"""Тести для SecureKeyManager."""

from __future__ import annotations

import os
from unittest.mock import patch

from src.utils.secure_key import SecureKeyManager


class TestSecureKeyManager:
    """Тести менеджера безпечного зберігання ключів."""

    def test_validate_key_format_valid(self) -> None:
        """Валідний формат ключа OpenAI."""
        assert SecureKeyManager.validate_key_format("sk-1234567890abcdefghijklmnop")
        assert SecureKeyManager.validate_key_format("sk-proj-abcdefghijklmnopqrstuvwxyz")

    def test_validate_key_format_invalid(self) -> None:
        """Невалідний формат ключа."""
        assert not SecureKeyManager.validate_key_format("")
        assert not SecureKeyManager.validate_key_format("invalid-key")
        assert not SecureKeyManager.validate_key_format("sk-short")

    def test_validate_groq_key_format(self) -> None:
        """Валiдний формат ключа Groq."""
        assert SecureKeyManager.validate_key_format("gsk_abcdefghijklmnopqrstuvwxyz", "groq")
        assert not SecureKeyManager.validate_key_format("sk-openai-key-here123", "groq")
        assert not SecureKeyManager.validate_key_format("gsk_short", "groq")

    def test_validate_deepgram_key_format(self) -> None:
        """Валiдний формат ключа Deepgram."""
        assert SecureKeyManager.validate_key_format("abcdefghijklmnopqrst", "deepgram")
        assert not SecureKeyManager.validate_key_format("short", "deepgram")

    def test_get_key_from_env(self) -> None:
        """Отримує ключ зі змінної оточення."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test1234567890abcdefg"}):
            key = SecureKeyManager.get_key()
            assert key == "sk-test1234567890abcdefg"

    def test_get_key_groq_from_env(self) -> None:
        """Отримує Groq ключ зі змiнної оточення."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test1234567890abcdefg"}):
            key = SecureKeyManager.get_key("groq")
            assert key == "gsk_test1234567890abcdefg"

    def test_get_key_none_when_not_configured(self) -> None:
        """Повертає None якщо ключ не налаштовано."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("src.utils.secure_key.keyring") as mock_kr,
            patch("src.utils.secure_key.load_dotenv"),
        ):
            mock_kr.get_password.return_value = None
            key = SecureKeyManager.get_key()
            assert key is None

    def test_is_configured_true(self) -> None:
        """is_configured повертає True коли ключ є."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test1234567890abcdefg"}):
            assert SecureKeyManager.is_configured()

    def test_is_configured_false(self) -> None:
        """is_configured повертає False коли ключа немає."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("src.utils.secure_key.keyring") as mock_kr,
            patch("src.utils.secure_key.load_dotenv"),
        ):
            mock_kr.get_password.return_value = None
            assert not SecureKeyManager.is_configured()

    def test_is_configured_groq(self) -> None:
        """is_configured для Groq."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test1234567890abcdefg"}):
            assert SecureKeyManager.is_configured("groq")

    def test_resolve_provider_keys(self) -> None:
        """Перевiрка резолвiнгу iмен ключiв по провайдеру."""
        assert SecureKeyManager._resolve("openai") == ("openai_api_key", "OPENAI_API_KEY")
        assert SecureKeyManager._resolve("groq") == ("groq_api_key", "GROQ_API_KEY")
        assert SecureKeyManager._resolve("deepgram") == ("deepgram_api_key", "DEEPGRAM_API_KEY")
        # Невiдомий провайдер -- fallback на openai
        assert SecureKeyManager._resolve("unknown") == ("openai_api_key", "OPENAI_API_KEY")
