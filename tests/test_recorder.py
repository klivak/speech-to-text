"""Тести для AudioRecorder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from src.core.recorder import AudioRecorder


class TestAudioRecorder:
    """Тести аудіо рекордера."""

    def test_initial_state(self) -> None:
        """Початковий стан рекордера."""
        recorder = AudioRecorder()
        assert not recorder.is_recording
        assert recorder.sample_rate == 16000

    def test_custom_sample_rate(self) -> None:
        """Кастомна частота дискретизації."""
        recorder = AudioRecorder(sample_rate=44100)
        assert recorder.sample_rate == 44100

    @patch("src.core.recorder.sd")
    def test_start_recording(self, mock_sd: MagicMock) -> None:
        """Запуск запису."""
        recorder = AudioRecorder()
        recorder.start()
        assert recorder.is_recording
        mock_sd.InputStream.assert_called_once()

    @patch("src.core.recorder.sd")
    def test_double_start_ignored(self, mock_sd: MagicMock) -> None:
        """Повторний запуск ігнорується."""
        recorder = AudioRecorder()
        recorder.start()
        recorder.start()
        # InputStream створюється тільки раз
        assert mock_sd.InputStream.call_count == 1

    @patch("src.core.recorder.sd")
    def test_stop_without_start(self, mock_sd: MagicMock) -> None:
        """Зупинка без запуску -- нічого не відбувається."""
        recorder = AudioRecorder()
        recorder.stop()  # не повинно викликати помилку
        assert not recorder.is_recording

    def test_get_input_devices(self) -> None:
        """Отримання списку пристроїв."""
        with patch("src.core.recorder.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {"name": "Mic 1", "max_input_channels": 1, "default_samplerate": 44100},
                {"name": "Speaker", "max_input_channels": 0, "default_samplerate": 44100},
            ]
            devices = AudioRecorder.get_input_devices()
            assert len(devices) == 1
            assert devices[0]["name"] == "Mic 1"

    def test_amplitude_calculation(self) -> None:
        """Тест обчислення амплітуди в callback."""
        recorder = AudioRecorder()
        recorder._is_recording = True
        amplitudes: list[float] = []
        recorder.amplitude_changed.connect(amplitudes.append)

        # Симулюємо callback з тестовими даними
        test_data = np.array([[0.1], [0.2], [-0.1], [0.15]], dtype=np.float32)
        recorder._audio_callback(test_data, 4, None, MagicMock(return_value=False))

        assert len(amplitudes) == 1
        assert 0.0 <= amplitudes[0] <= 1.0
