"""Головний клас додатку VoiceType -- координація всіх компонентів."""

from __future__ import annotations

import logging
import threading
from typing import Optional

import numpy as np
from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from src.audio.sounds import SoundManager, ensure_default_sounds
from src.config import ConfigManager
from src.constants import (
    DEVICE_AUTO,
    LANG_EN,
    LANG_UK,
    MODE_API,
    MODE_LOCAL,
    SUPPORTED_LANGUAGES,
)
from src.core.api_transcriber import APITranscriber
from src.core.dictionary import DictionaryManager
from src.core.history import HistoryManager
from src.core.hotkey_manager import HotkeyManager
from src.core.local_transcriber import LocalTranscriber
from src.core.recorder import AudioRecorder
from src.core.text_processor import TextProcessor
from src.core.transcriber import TranscriptionResult
from src.ui.floating_button import FloatingMicButton
from src.ui.history_window import HistoryWindow
from src.ui.overlay import RecordingOverlay
from src.ui.settings_window import SettingsWindow
from src.ui.themes.theme_manager import ThemeManager
from src.ui.tray import SystemTray
from src.utils.clipboard import paste_text
from src.utils.gpu_detect import get_available_devices, get_gpu_name
from src.utils.secure_key import SecureKeyManager

logger = logging.getLogger(__name__)


class VoiceTypeApp(QObject):
    """Головний клас додатку що координує всі компоненти.

    Зв'язує UI (трей, оверлей, налаштування) з логікою (запис, розпізнавання,
    обробка тексту) через сигнали та слоти PyQt6.
    """

    # Внутрішні сигнали для передачі результатів з потоків
    _transcription_done = pyqtSignal(object)
    _transcription_error = pyqtSignal(str)
    _benchmark_done = pyqtSignal(dict)

    def __init__(self, qt_app: QApplication) -> None:
        super().__init__()
        self._qt_app = qt_app

        # Конфігурація
        self._config = ConfigManager()

        # Створюємо дефолтні звуки
        ensure_default_sounds()

        # Ініціалізація компонентів
        self._init_theme()
        self._init_transcribers()
        self._init_audio()
        self._init_text_processing()
        self._init_ui()
        self._init_hotkeys()

        # Підключення внутрішніх сигналів (QueuedConnection для безпечної передачі з потоків)
        self._transcription_done.connect(
            self._on_transcription_done, Qt.ConnectionType.QueuedConnection
        )
        self._transcription_error.connect(
            self._on_transcription_error, Qt.ConnectionType.QueuedConnection
        )
        self._benchmark_done.connect(self._on_benchmark_done, Qt.ConnectionType.QueuedConnection)

        # Таймер перевірки завантаження моделі
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._check_model_loading)
        self._loading_timer.setInterval(500)
        self._loading_timer.start()
        self._loading_shown = False

        logger.info("VoiceType ініціалізовано. Режим: %s", self._config.get("mode"))

    def _init_theme(self) -> None:
        """Ініціалізація теми оформлення."""
        self._theme = ThemeManager(self._qt_app, self._config.get("app.theme", "system"))
        self._theme.apply_theme()

    def _init_transcribers(self) -> None:
        """Ініціалізація транскрайберів."""
        local_cfg = self._config.get_section("local")
        self._local_transcriber = LocalTranscriber(
            model_name=local_cfg.get("model", "small"),
            device=local_cfg.get("device", DEVICE_AUTO),
            fp16=local_cfg.get("fp16", False),
        )
        self._api_transcriber = APITranscriber(
            timeout=self._config.get("api.timeout", 30),
        )

    def _init_audio(self) -> None:
        """Ініціалізація аудіо компонентів."""
        self._recorder = AudioRecorder()
        self._recorder.amplitude_changed.connect(self._on_amplitude)
        self._recorder.recording_finished.connect(self._on_recording_finished)
        self._recorder.error_occurred.connect(self._on_recording_error)

        sounds_cfg = self._config.get_section("sounds")
        self._sounds = SoundManager(
            enabled=sounds_cfg.get("enabled", True),
            volume=sounds_cfg.get("volume", 0.5),
        )
        self._sounds.set_sound_enabled("start", sounds_cfg.get("on_start", True))
        self._sounds.set_sound_enabled("stop", sounds_cfg.get("on_stop", True))
        self._sounds.set_sound_enabled("success", sounds_cfg.get("on_success", True))
        self._sounds.set_sound_enabled("error", sounds_cfg.get("on_error", True))

    def _init_text_processing(self) -> None:
        """Ініціалізація обробки тексту."""
        text_cfg = self._config.get_section("text_processing")
        self._text_processor = TextProcessor(
            auto_capitalize=text_cfg.get("auto_capitalize", True),
            auto_period=text_cfg.get("auto_period", True),
            voice_commands_enabled=text_cfg.get("voice_commands_enabled", True),
        )
        self._dictionary = DictionaryManager()
        self._history = HistoryManager(
            max_items=self._config.get("app.max_history", 1000),
        )

    def _init_ui(self) -> None:
        """Ініціалізація UI компонентів."""
        mode = self._config.get("mode", MODE_LOCAL)
        language = self._config.get("language", LANG_UK)
        local_cfg = self._config.get_section("local")

        # Оверлей
        overlay_cfg = self._config.get_section("overlay")
        self._overlay: Optional[RecordingOverlay] = None
        if overlay_cfg.get("enabled", True):
            self._overlay = RecordingOverlay(
                size=overlay_cfg.get("size", "medium"),
                position=overlay_cfg.get("position", "center"),
                opacity=overlay_cfg.get("opacity", 0.8),
                show_text=overlay_cfg.get("show_text", True),
            )

        # Плаваюча кнопка
        fb_cfg = self._config.get_section("floating_button")
        self._floating_btn: Optional[FloatingMicButton] = None
        if fb_cfg.get("enabled", False):
            self._floating_btn = FloatingMicButton(
                size=fb_cfg.get("size", "medium"),
                position_x=fb_cfg.get("position_x", -1),
                position_y=fb_cfg.get("position_y", -1),
                is_dark_theme=self._theme.current_theme == "dark",
            )
            self._floating_btn.clicked.connect(self._on_floating_btn_click)
            self._floating_btn.settings_requested.connect(self._show_settings)
            self._floating_btn.hide_requested.connect(self._hide_floating_btn)
            self._floating_btn.show()

        # Системний трей
        self._tray = SystemTray(
            mode=mode,
            model=local_cfg.get("model", "small"),
            language=language,
            device=local_cfg.get("device", "cpu"),
        )
        self._tray.settings_requested.connect(self._show_settings)
        self._tray.history_requested.connect(self._show_history)
        self._tray.toggle_enabled.connect(self._toggle_enabled)
        self._tray.language_changed.connect(self._on_language_changed)
        self._tray.device_changed.connect(self._on_device_changed)
        self._tray.quit_requested.connect(self._quit)
        self._tray.show()

        # Вікна (створюються по запиту)
        self._settings_window: Optional[SettingsWindow] = None
        self._history_window: Optional[HistoryWindow] = None

        # Стан
        self._is_enabled = True

    def _init_hotkeys(self) -> None:
        """Ініціалізація гарячих клавіш."""
        hotkey_cfg = self._config.get_section("hotkey")
        self._hotkey_manager = HotkeyManager(
            hotkey=hotkey_cfg.get("record", "ctrl+shift"),
            mode=hotkey_cfg.get("mode", "push_to_talk"),
            language_hotkey=hotkey_cfg.get("switch_language", ""),
            device_hotkey=hotkey_cfg.get("switch_device", ""),
        )
        self._hotkey_manager.recording_start.connect(self._start_recording)
        self._hotkey_manager.recording_stop.connect(self._stop_recording)
        self._hotkey_manager.language_switch.connect(self._cycle_language)
        self._hotkey_manager.device_switch.connect(self._cycle_device)
        self._hotkey_manager.start()

    # ---- Запис та розпізнавання ----

    def _check_model_loading(self) -> None:
        """Перевіряє стан завантаження моделі та показує/ховає оверлей."""
        if self._config.get("mode") != MODE_LOCAL:
            if self._loading_shown:
                self._loading_shown = False
                if self._overlay:
                    self._overlay.hide_loading()
                self._tray.setToolTip(self._tray.toolTip().replace(" [завантаження...]", ""))
            return

        is_loading = self._local_transcriber.is_loading

        if is_loading and not self._loading_shown:
            # Почалось завантаження
            self._loading_shown = True
            model = self._local_transcriber.model_name
            if self._overlay:
                self._overlay.show_loading(f"Завантаження {model}...")
            self._tray.showMessage(
                "VoiceType",
                f"Завантаження моделi {model}...",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        elif not is_loading and self._loading_shown:
            # Завантаження завершилось
            self._loading_shown = False
            if self._overlay:
                self._overlay.hide_loading()
            error = self._local_transcriber._load_error
            if error:
                self._tray.showMessage(
                    "VoiceType",
                    f"Помилка завантаження: {error}",
                    QSystemTrayIcon.MessageIcon.Warning,
                    5000,
                )
            else:
                model = self._local_transcriber.model_name
                device = self._local_transcriber.current_device or "cpu"
                self._tray.showMessage(
                    "VoiceType",
                    f"Модель {model} готова ({device.upper()})",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,
                )

    @pyqtSlot()
    def _start_recording(self) -> None:
        """Починає запис з мікрофона."""
        if not self._is_enabled:
            return
        if self._recorder.is_recording:
            return

        logger.info("Початок запису...")
        self._sounds.play_start()
        self._recorder.start()

        if self._overlay:
            self._overlay.show_recording()

        self._tray.set_recording(True)
        if self._floating_btn:
            self._floating_btn.set_recording(True)

    @pyqtSlot()
    def _stop_recording(self) -> None:
        """Зупиняє запис та запускає розпізнавання."""
        if not self._recorder.is_recording:
            return

        logger.info("Зупинка запису...")
        self._sounds.play_stop()
        self._recorder.stop()

        self._tray.set_recording(False)
        if self._floating_btn:
            self._floating_btn.set_recording(False)

    @pyqtSlot(float)
    def _on_amplitude(self, amplitude: float) -> None:
        """Оновлює амплітуду в оверлеї."""
        if self._overlay:
            self._overlay.set_amplitude(amplitude)

    @pyqtSlot(object)
    def _on_recording_finished(self, audio_data: np.ndarray) -> None:
        """Обробляє записане аудіо -- запускає розпізнавання."""
        if self._overlay:
            self._overlay.show_processing()

        # Розпізнавання в окремому потоці
        thread = threading.Thread(
            target=self._transcribe_async,
            args=(audio_data,),
            daemon=True,
        )
        thread.start()

    @pyqtSlot(str)
    def _on_recording_error(self, error: str) -> None:
        """Обробляє помилку запису."""
        logger.error("Помилка запису: %s", error)
        self._sounds.play_error()
        if self._overlay:
            self._overlay.show_error(error)
        self._tray.set_recording(False)

    def _transcribe_async(self, audio: np.ndarray) -> None:
        """Виконує розпізнавання в окремому потоці."""
        try:
            language = self._config.get("language", LANG_UK)
            mode = self._config.get("mode", MODE_LOCAL)

            if mode == MODE_API:
                result = self._api_transcriber.transcribe(audio, language)
            else:
                result = self._local_transcriber.transcribe(audio, language)

            self._transcription_done.emit(result)
        except Exception as e:
            self._transcription_error.emit(str(e))

    @pyqtSlot(object)
    def _on_transcription_done(self, result: TranscriptionResult) -> None:
        """Обробляє результат розпізнавання (виконується в головному потоці)."""
        if result.is_empty:
            logger.warning("Розпізнавання не дало результату.")
            self._sounds.play_error()
            if self._overlay:
                self._overlay.show_error("Текст не розпiзнано")
            return

        # Постобробка тексту
        processed = self._text_processor.process(
            result.text,
            dictionary=self._dictionary.dictionary,
        )

        # Копіюємо в буфер обміну якщо увімкнено
        copy_to_clip = self._config.get("text_processing.copy_to_clipboard", True)
        if copy_to_clip:
            try:
                import pyperclip

                pyperclip.copy(processed)
                logger.info("Текст скопійовано в буфер: %s", processed[:80])
            except Exception as e:
                logger.warning("Не вдалось скопіювати в буфер: %s", e)

        # Вставка тексту
        logger.info("Вставка тексту: %s", processed[:80])
        success = paste_text(processed)

        if success:
            self._sounds.play_success()
            if self._overlay:
                self._overlay.show_success(processed)

            # Зберігаємо в історію
            result.text = processed
            self._history.add(result)
        else:
            self._sounds.play_error()
            if self._overlay:
                self._overlay.show_error("Помилка вставки")

    @pyqtSlot(str)
    def _on_transcription_error(self, error: str) -> None:
        """Обробляє помилку розпізнавання."""
        logger.error("Помилка розпізнавання: %s", error)
        self._sounds.play_error()
        if self._overlay:
            self._overlay.show_error("Помилка розпiзнавання")

    # ---- UI обробники ----

    def _on_floating_btn_click(self) -> None:
        """Обробник натискання плаваючої кнопки."""
        if self._recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _toggle_enabled(self) -> None:
        """Перемикає активність додатку."""
        self._is_enabled = not self._is_enabled
        if self._is_enabled:
            self._hotkey_manager.start()
        else:
            self._hotkey_manager.stop()
        self._tray.update_state(enabled=self._is_enabled)
        logger.info("Додаток %s.", "увімкнено" if self._is_enabled else "вимкнено")

    def _on_language_changed(self, language: str) -> None:
        """Обробник зміни мови."""
        self._config.set("language", language)
        self._tray.update_state(language=language)
        lang_name = SUPPORTED_LANGUAGES.get(language, language)
        logger.info("Мову змінено на: %s", lang_name)

    def _on_device_changed(self, device: str) -> None:
        """Обробник зміни пристрою."""
        self._config.set("local.device", device)
        self._local_transcriber.set_device(device)
        self._tray.update_state(device=device)
        logger.info("Пристрій змінено на: %s", device)

    def _cycle_language(self) -> None:
        """Перемикає мову по колу."""
        current = self._config.get("language", LANG_UK)
        new_lang = LANG_EN if current == LANG_UK else LANG_UK
        self._on_language_changed(new_lang)

    def _cycle_device(self) -> None:
        """Перемикає пристрій по колу."""
        current = self._local_transcriber.current_device
        new_device = "cpu" if current == "cuda" else "cuda"
        self._on_device_changed(new_device)

    def _hide_floating_btn(self) -> None:
        """Ховає плаваючу кнопку."""
        if self._floating_btn:
            self._floating_btn.hide()
            self._config.set("floating_button.enabled", False)

    # ---- Вікна ----

    def _show_settings(self) -> None:
        """Відкриває вікно налаштувань."""
        config_data = self._config.data
        self._settings_window = SettingsWindow(config_data)
        self._settings_window.settings_changed.connect(self._apply_settings)
        self._settings_window.api_key_test_requested.connect(self._test_api_key)
        self._settings_window.overlay_preview_requested.connect(self._preview_overlay)
        self._settings_window.model_download_requested.connect(self._download_model)
        self._settings_window.benchmark_requested.connect(self._run_benchmark)

        # Заповнюємо дані
        self._settings_window.load_dictionary(self._dictionary.dictionary)

        # GPU інфо
        gpu_name = get_gpu_name()
        if gpu_name:
            self._settings_window.set_gpu_info(gpu_name)
        else:
            self._settings_window.set_gpu_info("NVIDIA GPU не знайдено")

        # Статистика
        self._settings_window.update_stats(
            today=self._history.get_today_count(),
            total=self._history.get_total_count(),
            audio_duration=self._history.get_total_audio_duration(),
            avg_speed=self._history.get_average_processing_time(),
            popular_lang=self._history.get_most_used_language(),
        )

        self._settings_window.exec()

    def _show_history(self) -> None:
        """Відкриває вікно історії."""
        self._history_window = HistoryWindow(list(self._history.entries))
        self._history_window.entry_deleted.connect(self._history.delete)
        self._history_window.history_cleared.connect(self._history.clear)
        self._history_window.export_requested.connect(
            lambda path: self._history.export_to_txt(path)
        )
        self._history_window.exec()

    def _apply_settings(self, settings: dict) -> None:
        """Застосовує нові налаштування."""
        # Спеціальні дії
        action = settings.get("_action")
        if action == "import_dictionary":
            self._dictionary.import_from_file(settings["path"])
            return
        if action == "export_dictionary":
            self._dictionary.export_to_file(settings["path"])
            return
        if action == "reset_dictionary":
            self._dictionary.reset_to_defaults()
            return

        # Зберігаємо API ключ окремо
        if self._settings_window:
            api_key = self._settings_window.get_api_key()
            if api_key:
                SecureKeyManager.save_key(api_key)
                settings.setdefault("api", {})["api_key_configured"] = True
            elif not SecureKeyManager.is_configured():
                settings.setdefault("api", {})["api_key_configured"] = False

            # Зберігаємо словник
            new_dict = self._settings_window.get_dictionary()
            for spoken, written in new_dict.items():
                self._dictionary.add_word(spoken, written)

        # Оновлюємо конфігурацію
        for section, values in settings.items():
            if isinstance(values, dict):
                self._config.set_section(section, values)
            else:
                self._config.set(section, values)

        # Застосовуємо зміни
        self._apply_runtime_changes(settings)
        logger.info("Налаштування застосовано.")

    def _apply_runtime_changes(self, settings: dict) -> None:
        """Застосовує зміни що не потребують перезапуску."""
        # Тема
        app_settings = settings.get("app", {})
        if "theme" in app_settings:
            self._theme.apply_theme(app_settings["theme"])

        # Мова
        if "language" in settings:
            self._tray.update_state(language=settings["language"])

        # Режим
        if "mode" in settings:
            self._tray.update_state(mode=settings["mode"])

        # Локальний транскрайбер
        local_cfg = settings.get("local", {})
        if "model" in local_cfg:
            self._local_transcriber.set_model(local_cfg["model"])
        if "device" in local_cfg:
            self._local_transcriber.set_device(local_cfg["device"])
            self._tray.update_state(device=local_cfg["device"])
        if "fp16" in local_cfg:
            self._local_transcriber._fp16 = local_cfg["fp16"]

        # Гарячі клавіші
        hotkey_cfg = settings.get("hotkey", {})
        if "record" in hotkey_cfg or "mode" in hotkey_cfg:
            self._hotkey_manager.update_hotkey(
                hotkey_cfg.get("record", "ctrl+shift"),
                hotkey_cfg.get("mode", "push_to_talk"),
            )
        if "switch_language" in hotkey_cfg:
            self._hotkey_manager.update_language_hotkey(hotkey_cfg["switch_language"])
        if "switch_device" in hotkey_cfg:
            self._hotkey_manager.update_device_hotkey(hotkey_cfg["switch_device"])

        # Оверлей
        overlay_cfg = settings.get("overlay", {})
        if overlay_cfg.get("enabled", True) and self._overlay is None:
            self._overlay = RecordingOverlay()
        elif not overlay_cfg.get("enabled", True) and self._overlay:
            self._overlay.hide_overlay()
            self._overlay = None
        if self._overlay and overlay_cfg:
            self._overlay.update_settings(
                size=overlay_cfg.get("size"),
                position=overlay_cfg.get("position"),
                opacity=overlay_cfg.get("opacity"),
                show_text=overlay_cfg.get("show_text"),
            )

        # Плаваюча кнопка
        fb_cfg = settings.get("floating_button", {})
        if fb_cfg.get("enabled", False) and self._floating_btn is None:
            self._floating_btn = FloatingMicButton(
                is_dark_theme=self._theme.current_theme == "dark",
            )
            self._floating_btn.clicked.connect(self._on_floating_btn_click)
            self._floating_btn.settings_requested.connect(self._show_settings)
            self._floating_btn.hide_requested.connect(self._hide_floating_btn)
            self._floating_btn.show()
        elif not fb_cfg.get("enabled", False) and self._floating_btn:
            self._floating_btn.hide()
            self._floating_btn = None

        # Звуки
        sounds_cfg = settings.get("sounds", {})
        if sounds_cfg:
            self._sounds.enabled = sounds_cfg.get("enabled", True)
            self._sounds.volume = sounds_cfg.get("volume", 0.5)
            self._sounds.set_sound_enabled("start", sounds_cfg.get("on_start", True))
            self._sounds.set_sound_enabled("stop", sounds_cfg.get("on_stop", True))
            self._sounds.set_sound_enabled("success", sounds_cfg.get("on_success", True))
            self._sounds.set_sound_enabled("error", sounds_cfg.get("on_error", True))

        # Обробка тексту
        text_cfg = settings.get("text_processing", {})
        if text_cfg:
            self._text_processor.update_settings(
                auto_capitalize=text_cfg.get("auto_capitalize"),
                auto_period=text_cfg.get("auto_period"),
                voice_commands_enabled=text_cfg.get("voice_commands_enabled"),
            )

    def _test_api_key(self) -> None:
        """Тестує API ключ."""
        if self._settings_window:
            key = self._settings_window.get_api_key()
            if key:
                SecureKeyManager.save_key(key)

            success, message = self._api_transcriber.test_connection()
            self._settings_window.set_api_key_status(success, message)

    def _preview_overlay(self) -> None:
        """Показує попередній перегляд оверлею."""
        if self._overlay:
            self._overlay.preview()

    def _download_model(self, model_name: str) -> None:
        """Завантажує модель Whisper у фоні."""
        from src.utils.model_manager import download_model

        def _do_download() -> None:
            success = download_model(model_name)
            if success and self._settings_window:
                self._settings_window.set_model_status(model_name, True)

        thread = threading.Thread(target=_do_download, daemon=True)
        thread.start()

    def _run_benchmark(self) -> None:
        """Запускає бенчмарк транскрайбера у фоновому потоці."""
        if self._local_transcriber.is_loading:
            if self._settings_window:
                self._settings_window.set_benchmark_result(
                    {"error": "Модель ще завантажується, зачекайте..."}
                )
            return

        def _do_benchmark() -> None:
            result = self._local_transcriber.benchmark(duration_sec=5.0)
            self._benchmark_done.emit(result)

        thread = threading.Thread(target=_do_benchmark, daemon=True)
        thread.start()

        if self._settings_window:
            self._settings_window._bench_result_label.setText("Виконується benchmark...")
            self._settings_window._bench_result_label.setStyleSheet(
                "font-size: 13px; padding: 6px; color: #2196F3;"
            )

    @pyqtSlot(dict)
    def _on_benchmark_done(self, result: dict) -> None:
        """Обробляє результат бенчмарку (головний потік)."""
        if self._settings_window:
            self._settings_window.set_benchmark_result(result)

    # ---- Lifecycle ----

    def _quit(self) -> None:
        """Коректне завершення додатку."""
        logger.info("Завершення роботи VoiceType...")

        # Зупиняємо таймер перевірки завантаження
        self._loading_timer.stop()

        # Зупиняємо запис
        if self._recorder.is_recording:
            self._recorder.stop()

        # Зберігаємо позицію плаваючої кнопки
        if self._floating_btn and self._floating_btn.isVisible():
            x, y = self._floating_btn.get_position()
            self._config.set("floating_button.position_x", x)
            self._config.set("floating_button.position_y", y)

        # Зупиняємо гарячі клавіші
        self._hotkey_manager.stop()

        # Ховаємо UI
        self._tray.hide()
        if self._overlay:
            self._overlay.hide_overlay()
        if self._floating_btn:
            self._floating_btn.hide()

        self._qt_app.quit()
