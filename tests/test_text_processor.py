"""Тести для TextProcessor."""

from __future__ import annotations

from src.core.text_processor import TextProcessor


class TestTextProcessor:
    """Тести обробки тексту."""

    def test_auto_capitalize_first_letter(self) -> None:
        """Капіталізує перший символ тексту."""
        tp = TextProcessor(auto_capitalize=True, auto_period=False, voice_commands_enabled=False)
        assert tp.process("привіт") == "Привіт"

    def test_auto_capitalize_after_period(self) -> None:
        """Капіталізує після крапки."""
        tp = TextProcessor(auto_capitalize=True, auto_period=False, voice_commands_enabled=False)
        assert tp.process("перше речення. друге речення") == "Перше речення. Друге речення"

    def test_auto_period(self) -> None:
        """Додає крапку в кінці."""
        tp = TextProcessor(auto_capitalize=False, auto_period=True, voice_commands_enabled=False)
        assert tp.process("привіт світ") == "привіт світ."

    def test_auto_period_skips_existing(self) -> None:
        """Не додає крапку якщо вже є пунктуація."""
        tp = TextProcessor(auto_capitalize=False, auto_period=True, voice_commands_enabled=False)
        assert tp.process("привіт світ!") == "привіт світ!"
        assert tp.process("привіт світ?") == "привіт світ?"
        assert tp.process("привіт світ.") == "привіт світ."

    def test_voice_command_period(self) -> None:
        """Голосова команда 'крапка' замінюється на '.'."""
        tp = TextProcessor(auto_capitalize=False, auto_period=False, voice_commands_enabled=True)
        result = tp.process("привіт крапка як справи")
        assert "." in result
        assert "крапка" not in result

    def test_voice_command_comma(self) -> None:
        """Голосова команда 'кома' замінюється на ','."""
        tp = TextProcessor(auto_capitalize=False, auto_period=False, voice_commands_enabled=True)
        result = tp.process("привіт кома як справи")
        assert "," in result
        assert "кома" not in result

    def test_voice_command_question_mark(self) -> None:
        """Голосова команда 'знак питання'."""
        tp = TextProcessor(auto_capitalize=False, auto_period=False, voice_commands_enabled=True)
        result = tp.process("як справи знак питання")
        assert "?" in result

    def test_voice_command_new_line(self) -> None:
        """Голосова команда 'новий рядок'."""
        tp = TextProcessor(auto_capitalize=False, auto_period=False, voice_commands_enabled=True)
        result = tp.process("перший рядок новий рядок другий рядок")
        assert "\n" in result

    def test_voice_commands_disabled(self) -> None:
        """Голосові команди не застосовуються коли вимкнені."""
        tp = TextProcessor(auto_capitalize=False, auto_period=False, voice_commands_enabled=False)
        result = tp.process("привіт крапка")
        assert result == "привіт крапка"

    def test_english_voice_commands(self) -> None:
        """Англійські голосові команди."""
        tp = TextProcessor(auto_capitalize=False, auto_period=False, voice_commands_enabled=True)
        assert "." in tp.process("hello period")
        assert "," in tp.process("hello comma")
        assert "?" in tp.process("hello question mark")

    def test_dictionary_replacement(self) -> None:
        """Заміна слів зі словника."""
        tp = TextProcessor(auto_capitalize=False, auto_period=False, voice_commands_enabled=False)
        dictionary = {"пайтон": "Python", "реакт": "React"}
        result = tp.process("використовую пайтон та реакт", dictionary=dictionary)
        assert "Python" in result
        assert "React" in result
        assert "пайтон" not in result

    def test_dictionary_case_insensitive(self) -> None:
        """Словник працює без урахування регістру."""
        tp = TextProcessor(auto_capitalize=False, auto_period=False, voice_commands_enabled=False)
        dictionary = {"flutter": "Flutter"}
        result = tp.process("використовую Flutter для мобайл", dictionary=dictionary)
        assert "Flutter" in result

    def test_full_pipeline(self) -> None:
        """Повний конвеєр обробки."""
        tp = TextProcessor(auto_capitalize=True, auto_period=True, voice_commands_enabled=True)
        dictionary = {"пайтон": "Python"}
        result = tp.process(
            "використовую пайтон для розробки кома це дуже зручно",
            dictionary=dictionary,
        )
        assert result.startswith("В")  # Капіталізація
        assert "Python" in result  # Словник
        assert "," in result  # Голосова команда
        assert result.endswith(".")  # Авто-крапка

    def test_empty_text(self) -> None:
        """Порожній текст."""
        tp = TextProcessor()
        assert tp.process("") == ""

    def test_update_settings(self) -> None:
        """Оновлення налаштувань."""
        tp = TextProcessor(auto_capitalize=True)
        tp.update_settings(auto_capitalize=False)
        assert tp.process("привіт") == "привіт."
