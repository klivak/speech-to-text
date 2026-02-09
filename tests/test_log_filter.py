"""Тести для фільтра логів."""

from __future__ import annotations

from src.utils.log_filter import mask_api_key

# Тестовi ключi -- НЕ справжнi, використовуються тiльки для тестiв маскування
_FAKE_KEY = "sk-FAKE_TEST_KEY_00000000000"
_FAKE_KEY_PROJ = "sk-FAKE_TEST_proj_000000000000000000000000"
_FAKE_GROQ = "gsk_FAKE_TEST_KEY_00000000000000"


class TestLogFilter:
    """Тести маскування API ключів в логах."""

    def test_masks_api_key(self) -> None:
        """Маскує API ключ."""
        text = f"Using key {_FAKE_KEY}"
        result = mask_api_key(text)
        assert "FAKE_TEST" not in result
        assert "sk-..." in result

    def test_masks_multiple_keys(self) -> None:
        """Маскує кілька ключів в одному рядку."""
        text = f"key1={_FAKE_KEY} key2={_FAKE_KEY_PROJ}"
        result = mask_api_key(text)
        assert "FAKE_TEST" not in result
        assert result.count("sk-...") == 2

    def test_no_key_unchanged(self) -> None:
        """Текст без ключа залишається без змін."""
        text = "No API key here"
        assert mask_api_key(text) == text

    def test_preserves_surrounding_text(self) -> None:
        """Зберігає текст навколо ключа."""
        text = f"Before {_FAKE_KEY} After"
        result = mask_api_key(text)
        assert result.startswith("Before ")
        assert result.endswith(" After")

    def test_short_sk_not_masked(self) -> None:
        """Короткі рядки 'sk-' не маскуються."""
        text = "sk-short"
        assert mask_api_key(text) == text

    def test_empty_string(self) -> None:
        """Порожній рядок."""
        assert mask_api_key("") == ""

    def test_real_key_format(self) -> None:
        """Маскує ключ формату sk-proj-..."""
        result = mask_api_key(_FAKE_KEY_PROJ)
        assert "FAKE_TEST" not in result
        assert "sk-..." in result

    def test_masks_groq_key(self) -> None:
        """Маскує Groq API ключ."""
        text = f"Using key {_FAKE_GROQ}"
        result = mask_api_key(text)
        assert "FAKE_TEST" not in result
        assert "gsk_..." in result

    def test_masks_mixed_keys(self) -> None:
        """Маскує ключi рiзних провайдерiв."""
        text = f"openai={_FAKE_KEY} groq={_FAKE_GROQ}"
        result = mask_api_key(text)
        assert "FAKE_TEST" not in result
        assert "sk-..." in result
        assert "gsk_..." in result
