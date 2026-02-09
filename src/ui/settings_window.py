"""Вікно налаштувань з вкладками."""

from __future__ import annotations

import contextlib
import logging
import webbrowser
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.constants import (
    FLOAT_BUTTON_SIZES,
    OVERLAY_SIZES,
    SUPPORTED_LANGUAGES,
    WHISPER_MODELS,
)

logger = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    """Вікно налаштувань додатку з вкладками.

    Сигнали:
        settings_changed: dict -- налаштування змінено
        api_key_test_requested: тестування API ключа
        model_download_requested: str -- завантаження моделі
        benchmark_requested: тестування швидкості
        overlay_preview_requested: попередній перегляд оверлею
    """

    settings_changed = pyqtSignal(dict)
    api_key_test_requested = pyqtSignal()
    model_download_requested = pyqtSignal(str)
    benchmark_requested = pyqtSignal()
    overlay_preview_requested = pyqtSignal()

    def __init__(self, config: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config

        self.setWindowTitle("EchoScribe -- Налаштування")
        self.setMinimumSize(650, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Іконка вікна
        from PyQt6.QtGui import QColor

        from src.ui.tray import _create_colored_icon

        self.setWindowIcon(_create_colored_icon(QColor(124, 110, 240)))

        self._setup_ui()
        self._load_config()

    def _setup_ui(self) -> None:
        """Створює інтерфейс вікна."""
        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Вкладки
        self._tabs.addTab(self._create_general_tab(), "Загальне")
        self._tabs.addTab(self._create_api_tab(), "API")
        self._tabs.addTab(self._create_model_tab(), "Модель Whisper")
        self._tabs.addTab(self._create_hotkey_tab(), "Гарячi клавiшi")
        self._tabs.addTab(self._create_overlay_tab(), "Оверлей")
        self._tabs.addTab(self._create_sounds_tab(), "Звуки")
        self._tabs.addTab(self._create_text_tab(), "Текст")
        self._tabs.addTab(self._create_dictionary_tab(), "Словник")
        self._tabs.addTab(self._create_stats_tab(), "Статистика")

        # Кнопки внизу
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Зберегти")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Скасувати")
        cancel_btn.setProperty("flat", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ---- Вкладка "Загальне" ----

    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Режим
        mode_group = QGroupBox("Режим розпiзнавання")
        mode_layout = QVBoxLayout(mode_group)

        self._mode_local_radio = QCheckBox("Локальний (Offline) -- Whisper на вашому ПК")
        self._mode_api_radio = QCheckBox("API (Online) -- OpenAI Whisper API")
        self._mode_local_radio.setChecked(True)

        # Взаємовиключні
        self._mode_local_radio.toggled.connect(
            lambda checked: self._mode_api_radio.setChecked(not checked) if checked else None
        )
        self._mode_api_radio.toggled.connect(
            lambda checked: self._mode_local_radio.setChecked(not checked) if checked else None
        )

        mode_layout.addWidget(self._mode_local_radio)
        mode_layout.addWidget(self._mode_api_radio)
        layout.addWidget(mode_group)

        # Мова
        form = QFormLayout()
        self._language_combo = QComboBox()
        for code, name in SUPPORTED_LANGUAGES.items():
            self._language_combo.addItem(name, code)
        form.addRow("Мова розпiзнавання:", self._language_combo)

        # Тема
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Системна", "system")
        self._theme_combo.addItem("Свiтла", "light")
        self._theme_combo.addItem("Темна", "dark")
        form.addRow("Тема оформлення:", self._theme_combo)

        layout.addLayout(form)

        # Загальні опції
        self._autostart_check = QCheckBox("Автозапуск з Windows")
        self._minimize_tray_check = QCheckBox("Мiнiмiзувати в трей при закриттi")
        self._check_updates_check = QCheckBox("Перевiряти оновлення")

        layout.addWidget(self._autostart_check)
        layout.addWidget(self._minimize_tray_check)
        layout.addWidget(self._check_updates_check)
        layout.addStretch()

        return tab

    # ---- Вкладка "API" ----

    def _create_api_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "API ключ зберiгається безпечно в Windows Credential Manager, не в файлах проєкту."
        )
        info.setWordWrap(True)
        info.setProperty("class", "secondary")
        layout.addWidget(info)

        # API ключ
        key_layout = QHBoxLayout()
        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setPlaceholderText("sk-...")
        key_layout.addWidget(self._api_key_input)

        self._show_key_btn = QPushButton("Показати")
        self._show_key_btn.setFixedWidth(110)
        self._show_key_btn.clicked.connect(self._toggle_key_visibility)
        key_layout.addWidget(self._show_key_btn)

        layout.addLayout(key_layout)

        # Кнопки
        btn_layout = QHBoxLayout()

        test_btn = QPushButton("Перевiрити ключ")
        test_btn.clicked.connect(self.api_key_test_requested.emit)
        btn_layout.addWidget(test_btn)

        self._api_status_label = QLabel("")
        btn_layout.addWidget(self._api_status_label)
        btn_layout.addStretch()

        delete_btn = QPushButton("Видалити ключ")
        delete_btn.setProperty("flat", True)
        delete_btn.clicked.connect(self._delete_api_key)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

        # Посилання
        link_btn = QPushButton("Отримати API ключ на platform.openai.com")
        link_btn.setProperty("flat", True)
        link_btn.clicked.connect(lambda: webbrowser.open("https://platform.openai.com/api-keys"))
        layout.addWidget(link_btn)

        # Безпека
        security_group = QGroupBox("Безпека та конфiденцiйнiсть")
        security_layout = QVBoxLayout(security_group)
        security_info = QLabel(
            "-- API ключ зберiгається виключно в Windows Credential Manager (шифрування ОС)\n"
            "-- Ключ НIКОЛИ не зберiгається в config.json, логах або кодi\n"
            "-- В локальному режимi данi нiкуди не вiдправляються\n"
            "-- В режимi API аудiо надсилається тiльки на OpenAI для розпiзнавання\n"
            "-- Iсторiя зберiгається тiльки локально на вашому ПК\n"
            "-- Логи автоматично маскують будь-якi API ключi"
        )
        security_info.setWordWrap(True)
        security_info.setProperty("class", "secondary")
        security_layout.addWidget(security_info)
        layout.addWidget(security_group)

        layout.addStretch()
        return tab

    # ---- Вкладка "Модель Whisper" ----

    def _create_model_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Таблиця моделей
        self._model_table = QTableWidget(len(WHISPER_MODELS), 4)
        self._model_table.setHorizontalHeaderLabels(["Модель", "Розмiр", "Опис", "Статус"])
        self._model_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        self._model_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._model_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._model_table.setMinimumHeight(180)

        from src.utils.model_manager import is_model_downloaded

        for i, (name, info) in enumerate(WHISPER_MODELS.items()):
            self._model_table.setItem(i, 0, QTableWidgetItem(name))
            self._model_table.setItem(i, 1, QTableWidgetItem(f"{info['size_mb']} MB"))
            self._model_table.setItem(i, 2, QTableWidgetItem(info["description"]))  # type: ignore[call-overload]
            status = "Завантажено" if is_model_downloaded(name) else "Не завантажено"
            self._model_table.setItem(i, 3, QTableWidgetItem(status))

        layout.addWidget(self._model_table)

        # Завантаження моделі
        dl_layout = QHBoxLayout()
        download_btn = QPushButton("Завантажити модель")
        download_btn.clicked.connect(self._request_download)
        dl_layout.addWidget(download_btn)

        self._download_progress = QProgressBar()
        self._download_progress.setVisible(False)
        dl_layout.addWidget(self._download_progress)
        layout.addLayout(dl_layout)

        # Пристрій
        device_group = QGroupBox("Пристрiй обчислення")
        device_layout = QFormLayout(device_group)

        self._device_combo = QComboBox()
        self._device_combo.addItem("Автоматично", "auto")
        self._device_combo.addItem("CPU", "cpu")
        self._device_combo.addItem("CUDA GPU", "cuda")
        device_layout.addRow("Пристрiй:", self._device_combo)

        self._gpu_info_label = QLabel("Перевiрка GPU...")
        self._gpu_info_label.setProperty("class", "secondary")
        device_layout.addRow("GPU:", self._gpu_info_label)

        self._fp16_check = QCheckBox("fp16 (автоматично з GPU)")
        device_layout.addRow(self._fp16_check)

        layout.addWidget(device_group)

        # Benchmark
        bench_group = QGroupBox("Benchmark -- тест швидкостi")
        bench_layout = QVBoxLayout(bench_group)

        bench_info = QLabel(
            "Тест обробляє 5 секунд тестового аудiо та показує швидкiсть.\n"
            "RTF (Real-Time Factor) -- скiльки секунд аудiо обробляється за 1 секунду.\n"
            "RTF > 1.0 = швидше за реальний час, RTF < 1.0 = повiльнiше."
        )
        bench_info.setWordWrap(True)
        bench_info.setProperty("class", "secondary")
        bench_layout.addWidget(bench_info)

        bench_btn = QPushButton("Запустити benchmark")
        bench_btn.clicked.connect(self.benchmark_requested.emit)
        bench_layout.addWidget(bench_btn)

        self._bench_result_label = QLabel("")
        self._bench_result_label.setWordWrap(True)
        self._bench_result_label.setStyleSheet("font-size: 13px; padding: 6px;")
        bench_layout.addWidget(self._bench_result_label)

        # Таблиця порівняння (заповнюється ззовні)
        self._bench_table = QTableWidget(0, 3)
        self._bench_table.setHorizontalHeaderLabels(["Пристрiй", "Час обробки", "RTF"])
        self._bench_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        self._bench_table.setMaximumHeight(120)
        self._bench_table.setVisible(False)
        bench_layout.addWidget(self._bench_table)

        layout.addWidget(bench_group)

        return tab

    # ---- Вкладка "Гарячі клавіші" ----

    def _create_hotkey_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form = QFormLayout()

        # Основна комбінація
        self._hotkey_input = QLineEdit()
        self._hotkey_input.setPlaceholderText("Натиснiть комбiнацiю клавiш...")
        self._hotkey_input.setReadOnly(True)
        self._hotkey_input.mousePressEvent = lambda e: self._capture_hotkey(self._hotkey_input)  # type: ignore[method-assign,assignment]
        form.addRow("Запис:", self._hotkey_input)

        # Режим
        self._hotkey_mode_combo = QComboBox()
        self._hotkey_mode_combo.addItem("Push-to-talk (тримати)", "push_to_talk")
        self._hotkey_mode_combo.addItem("Toggle (натиснув-натиснув)", "toggle")
        form.addRow("Режим:", self._hotkey_mode_combo)

        # Додаткові комбінації
        self._lang_hotkey_input = QLineEdit()
        self._lang_hotkey_input.setPlaceholderText("Не призначено")
        self._lang_hotkey_input.setReadOnly(True)
        self._lang_hotkey_input.mousePressEvent = lambda e: self._capture_hotkey(  # type: ignore[method-assign,assignment]
            self._lang_hotkey_input
        )
        form.addRow("Перемикання мови:", self._lang_hotkey_input)

        self._device_hotkey_input = QLineEdit()
        self._device_hotkey_input.setPlaceholderText("Не призначено")
        self._device_hotkey_input.setReadOnly(True)
        self._device_hotkey_input.mousePressEvent = lambda e: self._capture_hotkey(  # type: ignore[method-assign,assignment]
            self._device_hotkey_input
        )
        form.addRow("Перемикання CPU/GPU:", self._device_hotkey_input)

        layout.addLayout(form)

        hint = QLabel("Натиснiть на поле та натиснiть потрiбну комбiнацiю клавiш.")
        hint.setProperty("class", "secondary")
        layout.addWidget(hint)

        layout.addStretch()
        return tab

    # ---- Вкладка "Оверлей" ----

    def _create_overlay_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._overlay_enabled_check = QCheckBox("Увiмкнути оверлей")
        layout.addWidget(self._overlay_enabled_check)

        form = QFormLayout()

        self._overlay_size_combo = QComboBox()
        for size_name in OVERLAY_SIZES:
            self._overlay_size_combo.addItem(size_name.capitalize(), size_name)
        form.addRow("Розмiр:", self._overlay_size_combo)

        self._overlay_position_combo = QComboBox()
        self._overlay_position_combo.addItem("Центр", "center")
        self._overlay_position_combo.addItem("Верх-центр", "top_center")
        self._overlay_position_combo.addItem("Низ-центр", "bottom_center")
        form.addRow("Позицiя:", self._overlay_position_combo)

        self._overlay_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._overlay_opacity_slider.setRange(20, 100)
        self._overlay_opacity_slider.setValue(80)
        form.addRow("Прозорiсть:", self._overlay_opacity_slider)

        self._overlay_show_text_check = QCheckBox("Показувати розпiзнаний текст")
        form.addRow(self._overlay_show_text_check)

        layout.addLayout(form)

        preview_btn = QPushButton("Попереднiй перегляд")
        preview_btn.clicked.connect(self.overlay_preview_requested.emit)
        layout.addWidget(preview_btn)

        # Плаваюча кнопка
        layout.addWidget(QLabel(""))  # spacer
        fb_group = QGroupBox("Плаваюча кнопка мiкрофона")
        fb_layout = QVBoxLayout(fb_group)

        self._floating_btn_check = QCheckBox("Увiмкнути плаваючу кнопку")
        fb_layout.addWidget(self._floating_btn_check)

        fb_form = QFormLayout()
        self._float_size_combo = QComboBox()
        for size_name in FLOAT_BUTTON_SIZES:
            self._float_size_combo.addItem(size_name.capitalize(), size_name)
        fb_form.addRow("Розмiр кнопки:", self._float_size_combo)
        fb_layout.addLayout(fb_form)

        layout.addWidget(fb_group)
        layout.addStretch()
        return tab

    # ---- Вкладка "Звуки" ----

    def _create_sounds_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._sounds_enabled_check = QCheckBox("Увiмкнути звуки")
        layout.addWidget(self._sounds_enabled_check)

        form = QFormLayout()

        # Набiр звукiв
        from src.audio.sounds import SOUND_PACKS

        self._sound_pack_combo = QComboBox()
        for key, label in SOUND_PACKS.items():
            self._sound_pack_combo.addItem(label, key)
        form.addRow("Набiр звукiв:", self._sound_pack_combo)

        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(50)
        form.addRow("Гучнiсть:", self._volume_slider)
        layout.addLayout(form)

        self._sound_start_check = QCheckBox("Початок запису")
        self._sound_stop_check = QCheckBox("Кiнець запису")
        self._sound_success_check = QCheckBox("Успiх розпiзнавання")
        self._sound_error_check = QCheckBox("Помилка")

        layout.addWidget(self._sound_start_check)
        layout.addWidget(self._sound_stop_check)
        layout.addWidget(self._sound_success_check)
        layout.addWidget(self._sound_error_check)

        layout.addStretch()
        return tab

    # ---- Вкладка "Текст" ----

    def _create_text_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._voice_commands_check = QCheckBox("Голосовi команди пунктуацiї")
        self._auto_capitalize_check = QCheckBox("Авто-капiталiзацiя")
        self._auto_period_check = QCheckBox("Авто-крапка в кiнцi")
        self._copy_clipboard_check = QCheckBox("Копiювати розпiзнаний текст в буфер обмiну")

        layout.addWidget(self._voice_commands_check)
        layout.addWidget(self._auto_capitalize_check)
        layout.addWidget(self._auto_period_check)
        layout.addWidget(self._copy_clipboard_check)

        # Таблиця команд пунктуації
        layout.addWidget(QLabel("Голосовi команди:"))

        self._punct_table = QTableWidget(0, 2)
        self._punct_table.setHorizontalHeaderLabels(["Команда", "Символ"])
        self._punct_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        layout.addWidget(self._punct_table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Додати")
        add_btn.clicked.connect(self._add_punct_row)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Видалити")
        remove_btn.setProperty("flat", True)
        remove_btn.clicked.connect(self._remove_punct_row)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return tab

    # ---- Вкладка "Словник" ----

    def _create_dictionary_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            "Словник застосовується пiсля розпiзнавання Whisper. "
            "Додавайте технiчнi термiни, назви фреймворкiв, та специфiчнi слова вашого проєкту."
        )
        info.setWordWrap(True)
        info.setProperty("class", "secondary")
        layout.addWidget(info)

        self._dict_table = QTableWidget(0, 2)
        self._dict_table.setHorizontalHeaderLabels(["Як вимовляється", "Правильний запис"])
        self._dict_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # type: ignore[union-attr]
        layout.addWidget(self._dict_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Додати слово")
        add_btn.clicked.connect(self._add_dict_row)
        btn_layout.addWidget(add_btn)

        import_btn = QPushButton("Iмпорт")
        import_btn.setProperty("flat", True)
        import_btn.clicked.connect(self._import_dictionary)
        btn_layout.addWidget(import_btn)

        export_btn = QPushButton("Експорт")
        export_btn.setProperty("flat", True)
        export_btn.clicked.connect(self._export_dictionary)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        reset_btn = QPushButton("Скинути до дефолтних")
        reset_btn.setProperty("flat", True)
        reset_btn.clicked.connect(self._reset_dictionary)
        btn_layout.addWidget(reset_btn)

        layout.addLayout(btn_layout)

        return tab

    # ---- Вкладка "Статистика" ----

    def _create_stats_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._stats_today_label = QLabel("Розпiзнавань сьогоднi: 0")
        self._stats_total_label = QLabel("Розпiзнавань всього: 0")
        self._stats_audio_label = QLabel("Загальний час аудiо: 0 сек")
        self._stats_speed_label = QLabel("Середня швидкiсть: 0 сек")
        self._stats_lang_label = QLabel("Найпопулярнiша мова: --")

        for label in [
            self._stats_today_label,
            self._stats_total_label,
            self._stats_audio_label,
            self._stats_speed_label,
            self._stats_lang_label,
        ]:
            label.setStyleSheet("font-size: 14px; padding: 4px;")
            layout.addWidget(label)

        # Графік (placeholder)
        self._chart_widget = QWidget()
        self._chart_widget.setMinimumHeight(150)
        layout.addWidget(self._chart_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        reset_btn = QPushButton("Скинути статистику")
        reset_btn.setProperty("flat", True)
        btn_layout.addWidget(reset_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()
        return tab

    # ---- Завантаження/збереження конфігурації ----

    def _load_config(self) -> None:
        """Завантажує налаштування з конфігурації в елементи UI."""
        c = self._config

        # Загальне
        self._mode_local_radio.setChecked(c.get("mode") == "local")
        self._mode_api_radio.setChecked(c.get("mode") == "api")

        lang = c.get("language", "uk")
        idx = self._language_combo.findData(lang)
        if idx >= 0:
            self._language_combo.setCurrentIndex(idx)

        theme = c.get("app", {}).get("theme", "system")
        idx = self._theme_combo.findData(theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)

        app = c.get("app", {})
        self._autostart_check.setChecked(app.get("autostart", False))
        self._minimize_tray_check.setChecked(app.get("minimize_to_tray", True))
        self._check_updates_check.setChecked(app.get("check_updates", True))

        # Модель
        local = c.get("local", {})
        device = local.get("device", "auto")
        idx = self._device_combo.findData(device)
        if idx >= 0:
            self._device_combo.setCurrentIndex(idx)
        self._fp16_check.setChecked(local.get("fp16", False))

        # Гарячі клавіші
        hotkey = c.get("hotkey", {})
        self._hotkey_input.setText(hotkey.get("record", "ctrl+shift"))
        mode = hotkey.get("mode", "push_to_talk")
        idx = self._hotkey_mode_combo.findData(mode)
        if idx >= 0:
            self._hotkey_mode_combo.setCurrentIndex(idx)
        self._lang_hotkey_input.setText(hotkey.get("switch_language", ""))
        self._device_hotkey_input.setText(hotkey.get("switch_device", ""))

        # Оверлей
        overlay = c.get("overlay", {})
        self._overlay_enabled_check.setChecked(overlay.get("enabled", True))
        idx = self._overlay_size_combo.findData(overlay.get("size", "medium"))
        if idx >= 0:
            self._overlay_size_combo.setCurrentIndex(idx)
        idx = self._overlay_position_combo.findData(overlay.get("position", "center"))
        if idx >= 0:
            self._overlay_position_combo.setCurrentIndex(idx)
        self._overlay_opacity_slider.setValue(int(overlay.get("opacity", 0.8) * 100))
        self._overlay_show_text_check.setChecked(overlay.get("show_text", True))

        # Плаваюча кнопка
        fb = c.get("floating_button", {})
        self._floating_btn_check.setChecked(fb.get("enabled", False))
        idx = self._float_size_combo.findData(fb.get("size", "medium"))
        if idx >= 0:
            self._float_size_combo.setCurrentIndex(idx)

        # Звуки
        sounds = c.get("sounds", {})
        self._sounds_enabled_check.setChecked(sounds.get("enabled", True))
        pack = sounds.get("pack", "standard")
        idx = self._sound_pack_combo.findData(pack)
        if idx >= 0:
            self._sound_pack_combo.setCurrentIndex(idx)
        self._volume_slider.setValue(int(sounds.get("volume", 0.5) * 100))
        self._sound_start_check.setChecked(sounds.get("on_start", True))
        self._sound_stop_check.setChecked(sounds.get("on_stop", True))
        self._sound_success_check.setChecked(sounds.get("on_success", True))
        self._sound_error_check.setChecked(sounds.get("on_error", True))

        # Текст
        text = c.get("text_processing", {})
        self._voice_commands_check.setChecked(text.get("voice_commands_enabled", True))
        self._auto_capitalize_check.setChecked(text.get("auto_capitalize", True))
        self._auto_period_check.setChecked(text.get("auto_period", True))
        self._copy_clipboard_check.setChecked(text.get("copy_to_clipboard", True))

    def _save_settings(self) -> None:
        """Зберігає налаштування та закриває вікно."""
        settings = {
            "mode": "local" if self._mode_local_radio.isChecked() else "api",
            "language": self._language_combo.currentData(),
            "local": {
                "model": self._get_selected_model(),
                "device": self._device_combo.currentData(),
                "fp16": self._fp16_check.isChecked(),
            },
            "hotkey": {
                "record": self._hotkey_input.text() or "ctrl+shift",
                "mode": self._hotkey_mode_combo.currentData(),
                "switch_language": self._lang_hotkey_input.text(),
                "switch_device": self._device_hotkey_input.text(),
            },
            "overlay": {
                "enabled": self._overlay_enabled_check.isChecked(),
                "size": self._overlay_size_combo.currentData(),
                "position": self._overlay_position_combo.currentData(),
                "opacity": self._overlay_opacity_slider.value() / 100.0,
                "show_text": self._overlay_show_text_check.isChecked(),
            },
            "floating_button": {
                "enabled": self._floating_btn_check.isChecked(),
                "size": self._float_size_combo.currentData(),
            },
            "sounds": {
                "enabled": self._sounds_enabled_check.isChecked(),
                "pack": self._sound_pack_combo.currentData(),
                "volume": self._volume_slider.value() / 100.0,
                "on_start": self._sound_start_check.isChecked(),
                "on_stop": self._sound_stop_check.isChecked(),
                "on_success": self._sound_success_check.isChecked(),
                "on_error": self._sound_error_check.isChecked(),
            },
            "text_processing": {
                "voice_commands_enabled": self._voice_commands_check.isChecked(),
                "auto_capitalize": self._auto_capitalize_check.isChecked(),
                "auto_period": self._auto_period_check.isChecked(),
                "copy_to_clipboard": self._copy_clipboard_check.isChecked(),
            },
            "app": {
                "autostart": self._autostart_check.isChecked(),
                "minimize_to_tray": self._minimize_tray_check.isChecked(),
                "check_updates": self._check_updates_check.isChecked(),
                "theme": self._theme_combo.currentData(),
            },
        }

        self.settings_changed.emit(settings)
        self.accept()

    def _get_selected_model(self) -> str:
        """Повертає назву обраної моделі з таблиці."""
        selected = self._model_table.selectedItems()
        if selected:
            row = selected[0].row()
            item = self._model_table.item(row, 0)
            if item:
                return item.text()
        return self._config.get("local", {}).get("model", "small")  # type: ignore[no-any-return]

    # ---- Допоміжні методи ----

    def _toggle_key_visibility(self) -> None:
        """Перемикає видимість API ключа."""
        if self._api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_key_btn.setText("Сховати")
        else:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_key_btn.setText("Показати")

    def _delete_api_key(self) -> None:
        """Видаляє API ключ з підтвердженням."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Видалити API ключ")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("Ви впевненi що хочете видалити API ключ?")
        yes_btn = msg.addButton("Так", QMessageBox.ButtonRole.YesRole)
        msg.addButton("Нi", QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() == yes_btn:
            self._api_key_input.clear()
            from src.utils.secure_key import SecureKeyManager

            SecureKeyManager.delete_key()
            self._api_status_label.setText("Ключ видалено")

    def _capture_hotkey(self, input_field: QLineEdit) -> None:
        """Захоплює комбінацію клавіш для поля вводу."""
        input_field.setText("Натиснiть комбiнацiю...")
        input_field.setFocus()

        import keyboard

        def on_key(event: keyboard.KeyboardEvent) -> None:
            if event.event_type == "down":
                modifiers = []
                if keyboard.is_pressed("ctrl"):
                    modifiers.append("ctrl")
                if keyboard.is_pressed("shift"):
                    modifiers.append("shift")
                if keyboard.is_pressed("alt"):
                    modifiers.append("alt")

                key = event.name
                if key not in ("ctrl", "shift", "alt", "unknown"):
                    combo = "+".join(modifiers + [key]) if modifiers else key
                    input_field.setText(combo)
                    keyboard.unhook(hook)

        hook = keyboard.hook(on_key)

        # Автоочищення хука через 10 секунд як fallback
        def _cleanup_hook() -> None:
            with contextlib.suppress(Exception):
                keyboard.unhook(hook)

        QTimer.singleShot(10000, _cleanup_hook)

    def _request_download(self) -> None:
        """Запитує завантаження обраної моделі."""
        model = self._get_selected_model()
        self.model_download_requested.emit(model)

    def _add_punct_row(self) -> None:
        """Додає порожній рядок в таблицю пунктуації."""
        row = self._punct_table.rowCount()
        self._punct_table.insertRow(row)

    def _remove_punct_row(self) -> None:
        """Видаляє обраний рядок з таблиці пунктуації."""
        row = self._punct_table.currentRow()
        if row >= 0:
            self._punct_table.removeRow(row)

    def _add_dict_row(self) -> None:
        """Додає порожній рядок в таблицю словника."""
        row = self._dict_table.rowCount()
        self._dict_table.insertRow(row)

    def _import_dictionary(self) -> None:
        """Імпортує словник з JSON файлу."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Iмпорт словника", "", "JSON (*.json)")
        if file_path:
            self.settings_changed.emit({"_action": "import_dictionary", "path": file_path})

    def _export_dictionary(self) -> None:
        """Експортує словник в JSON файл."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Експорт словника", "dictionary.json", "JSON (*.json)"
        )
        if file_path:
            self.settings_changed.emit({"_action": "export_dictionary", "path": file_path})

    def _reset_dictionary(self) -> None:
        """Скидає словник до дефолтних значень."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Скинути словник")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("Скинути словник до дефолтних значень? Всi кастомнi записи будуть видаленi.")
        yes_btn = msg.addButton("Так", QMessageBox.ButtonRole.YesRole)
        msg.addButton("Нi", QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() == yes_btn:
            self.settings_changed.emit({"_action": "reset_dictionary"})

    # ---- Публічні методи для оновлення ----

    def set_api_key_status(self, success: bool, message: str) -> None:
        """Встановлює статус перевірки API ключа."""
        color = "green" if success else "red"
        self._api_status_label.setStyleSheet(f"color: {color};")
        self._api_status_label.setText(message)

    def set_gpu_info(self, info: str) -> None:
        """Встановлює інформацію про GPU."""
        self._gpu_info_label.setText(info)

    def set_model_status(self, model: str, downloaded: bool) -> None:
        """Оновлює статус моделі в таблиці."""
        for i in range(self._model_table.rowCount()):
            item = self._model_table.item(i, 0)
            if item and item.text() == model:
                status = "Завантажено" if downloaded else "Потрiбно завантажити"
                self._model_table.setItem(i, 3, QTableWidgetItem(status))
                break

    def update_stats(
        self,
        today: int = 0,
        total: int = 0,
        audio_duration: float = 0,
        avg_speed: float = 0,
        popular_lang: str = "--",
    ) -> None:
        """Оновлює вкладку статистики."""
        self._stats_today_label.setText(f"Розпiзнавань сьогоднi: {today}")
        self._stats_total_label.setText(f"Розпiзнавань всього: {total}")
        self._stats_audio_label.setText(
            f"Загальний час аудiо: {audio_duration:.0f} сек ({audio_duration / 60:.1f} хв)"
        )
        self._stats_speed_label.setText(f"Середня швидкiсть: {avg_speed:.1f} сек")
        lang_name = SUPPORTED_LANGUAGES.get(popular_lang, popular_lang)
        self._stats_lang_label.setText(f"Найпопулярнiша мова: {lang_name}")

    def load_dictionary(self, dictionary: dict[str, str]) -> None:
        """Завантажує словник в таблицю."""
        self._dict_table.setRowCount(0)
        for spoken, written in dictionary.items():
            row = self._dict_table.rowCount()
            self._dict_table.insertRow(row)
            self._dict_table.setItem(row, 0, QTableWidgetItem(spoken))
            self._dict_table.setItem(row, 1, QTableWidgetItem(written))

    def get_dictionary(self) -> dict[str, str]:
        """Отримує словник з таблиці."""
        result: dict[str, str] = {}
        for row in range(self._dict_table.rowCount()):
            spoken_item = self._dict_table.item(row, 0)
            written_item = self._dict_table.item(row, 1)
            if spoken_item and written_item:
                spoken = spoken_item.text().strip()
                written = written_item.text().strip()
                if spoken and written:
                    result[spoken] = written
        return result

    def set_benchmark_result(self, result: dict) -> None:
        """Показує результат бенчмарку."""
        if "error" in result:
            self._bench_result_label.setText(f"Помилка: {result['error']}")
            self._bench_result_label.setStyleSheet("font-size: 13px; padding: 6px; color: red;")
            return

        device = result.get("device", "?")
        model = result.get("model", "?")
        proc_time = result.get("processing_time", 0)
        rtf = result.get("realtime_factor", 0)
        audio_dur = result.get("audio_duration", 5)

        if rtf >= 1.0:
            speed_text = f"Швидше за реальний час ({rtf:.1f}x)"
            color = "#4CAF50"
        else:
            speed_text = f"Повiльнiше за реальний час ({rtf:.1f}x)"
            color = "#FF9800"

        self._bench_result_label.setText(
            f"Модель: {model} | Пристрiй: {device.upper()}\n"
            f"{audio_dur:.0f} сек аудiо оброблено за {proc_time:.1f} сек\n"
            f"{speed_text}"
        )
        self._bench_result_label.setStyleSheet(f"font-size: 13px; padding: 6px; color: {color};")

        # Додаємо рядок до таблиці порівняння
        self._bench_table.setVisible(True)
        row = self._bench_table.rowCount()
        self._bench_table.insertRow(row)
        self._bench_table.setItem(row, 0, QTableWidgetItem(f"{device.upper()} ({model})"))
        self._bench_table.setItem(row, 1, QTableWidgetItem(f"{proc_time:.1f} сек"))
        rtf_item = QTableWidgetItem(f"{rtf:.2f}x")
        self._bench_table.setItem(row, 2, rtf_item)

    def get_api_key(self) -> str:
        """Повертає введений API ключ."""
        return self._api_key_input.text().strip()
