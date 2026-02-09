"""Менеджер глобальних гарячих клавіш."""

from __future__ import annotations

import contextlib
import logging
import threading
from typing import Callable

import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

from src.constants import DEFAULT_HOTKEY, HOTKEY_MODE_PUSH, HOTKEY_MODE_TOGGLE

logger = logging.getLogger(__name__)

# Затримка перед початком запису (мс), щоб уникнути конфлiкту
# з комбiнацiями типу ctrl+shift+x
_PUSH_DELAY_MS = 200


class HotkeyManager(QObject):
    """Менеджер глобальних гарячих клавіш.

    Підтримує два режими:
    - Push-to-talk: тримаємо клавішу для запису
    - Toggle: натиснув -- почалося, натиснув -- зупинилось

    Сигнали:
        recording_start: запис починається
        recording_stop: запис зупиняється
        language_switch: перемикання мови
        device_switch: перемикання CPU/GPU
    """

    recording_start = pyqtSignal()
    recording_stop = pyqtSignal()
    language_switch = pyqtSignal()
    device_switch = pyqtSignal()

    def __init__(
        self,
        hotkey: str = DEFAULT_HOTKEY,
        mode: str = HOTKEY_MODE_PUSH,
        language_hotkey: str = "",
        device_hotkey: str = "",
    ) -> None:
        super().__init__()
        self._hotkey = hotkey
        self._mode = mode
        self._language_hotkey = language_hotkey
        self._device_hotkey = device_hotkey
        self._is_recording = False
        self._is_active = False
        self._lock = threading.Lock()
        self._hooks: list[Callable] = []
        self._pending_start = False
        self._extra_key_pressed = False
        self._all_keys_hook: Callable | None = None
        self._delay_timer: threading.Timer | None = None

    @property
    def is_recording(self) -> bool:
        """Чи активний запис."""
        return self._is_recording

    @property
    def is_active(self) -> bool:
        """Чи активний менеджер гарячих клавіш."""
        return self._is_active

    def start(self) -> None:
        """Активує глобальні гарячі клавіші."""
        if self._is_active:
            return

        self._register_hotkeys()
        self._is_active = True
        logger.info("Гарячі клавіші активовано. Основна: %s (%s)", self._hotkey, self._mode)

    def stop(self) -> None:
        """Деактивує глобальні гарячі клавіші."""
        if not self._is_active:
            return

        self._unregister_hotkeys()
        self._is_active = False
        with self._lock:
            self._is_recording = False
        logger.info("Гарячі клавіші деактивовано.")

    def update_hotkey(self, hotkey: str, mode: str) -> None:
        """Оновлює основну гарячу клавішу."""
        was_active = self._is_active
        if was_active:
            self.stop()

        self._hotkey = hotkey
        self._mode = mode

        if was_active:
            self.start()

    def update_language_hotkey(self, hotkey: str) -> None:
        """Оновлює гарячу клавішу перемикання мови."""
        was_active = self._is_active
        if was_active:
            self.stop()

        self._language_hotkey = hotkey

        if was_active:
            self.start()

    def update_device_hotkey(self, hotkey: str) -> None:
        """Оновлює гарячу клавішу перемикання пристрою."""
        was_active = self._is_active
        if was_active:
            self.stop()

        self._device_hotkey = hotkey

        if was_active:
            self.start()

    def _parse_hotkey_parts(self) -> tuple[list[str], str]:
        """Розбирає комбінацію на модифікатори та основну клавішу.

        Для комбінацій типу "ctrl+shift" останній елемент -- основна клавіша.
        Якщо всі елементи є модифікаторами, останній модифікатор виступає
        як тригер, а решта -- як умови.
        """
        parts = [p.strip().lower() for p in self._hotkey.split("+")]
        if len(parts) == 1:
            return [], parts[0]
        return parts[:-1], parts[-1]

    def _register_hotkeys(self) -> None:
        """Реєструє гарячі клавіші в системі."""
        self._unregister_hotkeys()

        if self._mode == HOTKEY_MODE_PUSH:
            modifiers, trigger_key = self._parse_hotkey_parts()

            # Push-to-talk: слідкуємо за натисканням/відпусканням тригерної клавіші
            # та перевіряємо модифікатори
            hook_press = keyboard.on_press_key(
                trigger_key,
                self._on_push_press,
                suppress=False,
            )
            hook_release = keyboard.on_release_key(
                trigger_key,
                self._on_push_release,
                suppress=False,
            )
            self._hooks.extend([hook_press, hook_release])
        elif self._mode == HOTKEY_MODE_TOGGLE:
            # Toggle: натиснув-натиснув
            hotkey_hook = keyboard.add_hotkey(self._hotkey, self._on_toggle, suppress=False)
            self._hooks.append(hotkey_hook)

        # Додаткові гарячі клавіші
        if self._language_hotkey:
            lang_hook = keyboard.add_hotkey(
                self._language_hotkey,
                self._on_language_switch,
                suppress=False,
            )
            self._hooks.append(lang_hook)

        if self._device_hotkey:
            dev_hook = keyboard.add_hotkey(
                self._device_hotkey,
                self._on_device_switch,
                suppress=False,
            )
            self._hooks.append(dev_hook)

    def _unregister_hotkeys(self) -> None:
        """Знімає всі зареєстровані гарячі клавіші."""
        for hook in self._hooks:
            try:
                keyboard.unhook(hook)
            except (ValueError, KeyError):
                pass
            except Exception as e:
                logger.debug("Помилка при знятті гарячої клавіші: %s", e)
        self._hooks.clear()

    def _check_modifiers(self) -> bool:
        """Перевіряє чи натиснуті модифікатори з комбінації."""
        modifiers, _ = self._parse_hotkey_parts()

        if not modifiers:
            return True

        for mod in modifiers:
            try:
                if not keyboard.is_pressed(mod):
                    return False
            except ValueError:
                logger.warning("Невідомий модифікатор: %s", mod)
                return False
        return True

    def _on_push_press(self, event: keyboard.KeyboardEvent) -> None:
        """Обробник натискання в режимі push-to-talk.

        Використовує затримку щоб не конфлiктувати з комбiнацiями
        типу ctrl+shift+x. Якщо пiсля натискання тригера протягом
        _PUSH_DELAY_MS натиснута iнша клавiша -- запис скасовується.
        """
        with self._lock:
            if self._is_recording or not self._check_modifiers():
                return
            self._pending_start = True
            self._extra_key_pressed = False

        # Слiдкуємо за iншими клавiшами пiд час затримки
        modifiers, trigger_key = self._parse_hotkey_parts()
        ignore_keys = set(modifiers + [trigger_key])

        def _on_any_key(e: keyboard.KeyboardEvent) -> None:
            if e.event_type == "down" and e.name and e.name.lower() not in ignore_keys:
                self._extra_key_pressed = True

        self._all_keys_hook = keyboard.hook(_on_any_key)

        # Запуск таймера затримки
        self._delay_timer = threading.Timer(_PUSH_DELAY_MS / 1000.0, self._on_delay_finished)
        self._delay_timer.daemon = True
        self._delay_timer.start()

    def _on_delay_finished(self) -> None:
        """Викликається пiсля затримки -- починає запис якщо не було iнших клавiш."""
        # Знiмаємо хук на всi клавiшi
        if self._all_keys_hook is not None:
            with contextlib.suppress(ValueError, KeyError):
                keyboard.unhook(self._all_keys_hook)
            self._all_keys_hook = None

        with self._lock:
            if self._pending_start and not self._extra_key_pressed:
                self._is_recording = True
                self._pending_start = False
                self.recording_start.emit()
            else:
                self._pending_start = False

    def _on_push_release(self, event: keyboard.KeyboardEvent) -> None:
        """Обробник відпускання в режимі push-to-talk."""
        # Скасувати очiкування якщо вiдпустили до закiнчення затримки
        if self._pending_start:
            self._pending_start = False
            if self._delay_timer is not None:
                self._delay_timer.cancel()
            if self._all_keys_hook is not None:
                with contextlib.suppress(ValueError, KeyError):
                    keyboard.unhook(self._all_keys_hook)
                self._all_keys_hook = None
            return

        with self._lock:
            if self._is_recording:
                self._is_recording = False
                self.recording_stop.emit()

    def _on_toggle(self) -> None:
        """Обробник натискання в режимі toggle."""
        with self._lock:
            if self._is_recording:
                self._is_recording = False
                self.recording_stop.emit()
            else:
                self._is_recording = True
                self.recording_start.emit()

    def _on_language_switch(self) -> None:
        """Обробник перемикання мови."""
        self.language_switch.emit()

    def _on_device_switch(self) -> None:
        """Обробник перемикання пристрою."""
        self.device_switch.emit()
