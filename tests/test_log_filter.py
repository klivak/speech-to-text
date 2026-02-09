"""Тести для фільтра логів."""

from __future__ import annotations

from src.utils.log_filter import mask_api_key


class TestLogFilter:
    """Тести маскування API ключів в логах."""

    def test_masks_api_key(self) -> None:
        """Маскує API ключ."""
        text = "Using key sk-1234567890abcdefghijklmnop"
        result = mask_api_key(text)
        assert "sk-1234567890" not in result
        assert "sk-...mnop" in result

    def test_masks_multiple_keys(self) -> None:
        """Маскує кілька ключів в одному рядку."""
        text = "key1=sk-aaaaaaaaaaaaaaaaaaaaaa key2=sk-bbbbbbbbbbbbbbbbbbbbbb"
        result = mask_api_key(text)
        assert "sk-aaa" not in result
        assert "sk-bbb" not in result
        assert result.count("sk-...") == 2

    def test_no_key_unchanged(self) -> None:
        """Текст без ключа залишається без змін."""
        text = "No API key here"
        assert mask_api_key(text) == text

    def test_preserves_surrounding_text(self) -> None:
        """Зберігає текст навколо ключа."""
        text = "Before sk-1234567890abcdefghijklmnop After"
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
        """Маскує ключ реального формату."""
        text = "sk-FAKE_REDACTED"
        result = mask_api_key(text)
        assert "proj-abc" not in result
        assert "sk-..." in result
