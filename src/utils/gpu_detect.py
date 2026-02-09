"""Автодетект CUDA GPU та інформація про пристрої."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def is_cuda_available() -> bool:
    """Перевіряє доступність CUDA GPU."""
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


def get_gpu_name() -> str | None:
    """Повертає назву NVIDIA GPU або None."""
    try:
        import torch

        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
    except Exception:
        pass
    return None


def get_gpu_vram_gb() -> float | None:
    """Повертає обсяг VRAM в гігабайтах або None."""
    try:
        import torch

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return float(props.total_memory / (1024**3))
    except Exception:
        pass
    return None


def get_available_devices() -> list[dict[str, object]]:
    """Повертає список доступних пристроїв з інформацією."""
    devices: list[dict[str, object]] = [
        {"id": "cpu", "name": "CPU", "available": True},
    ]

    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            devices.append(
                {
                    "id": "cuda",
                    "name": f"{gpu_name} ({vram:.1f} GB VRAM)",
                    "available": True,
                }
            )
        else:
            devices.append(
                {
                    "id": "cuda",
                    "name": "CUDA недоступний",
                    "available": False,
                }
            )
    except Exception:
        devices.append(
            {
                "id": "cuda",
                "name": "CUDA недоступний (torch без GPU)",
                "available": False,
            }
        )

    return devices


def get_optimal_device() -> str:
    """Визначає оптимальний пристрій для обчислень."""
    if is_cuda_available():
        logger.info("CUDA GPU доступний: %s", get_gpu_name())
        return "cuda"
    logger.info("CUDA GPU недоступний, використовуємо CPU.")
    return "cpu"
