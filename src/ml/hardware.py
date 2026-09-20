"""Hardware device auto-detection and optimal precision negotiation (CUDA/MPS/DirectML/CPU)."""

from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)

_GLOBAL_HARDWARE_MANAGER: HardwareDeviceManager | None = None


class HardwareDeviceManager:
    """
    Auto-detects host ML hardware acceleration (NVIDIA CUDA, Apple Silicon MPS, DirectML, or CPU)
    and selects the optimal numerical precision (FP16/INT8) to minimize VRAM footprint.
    """

    def __init__(self) -> None:
        self._device: str = "cpu"
        self._dtype: str = "float32"
        self._device_name: str = "CPU"
        self._detect_hardware()

    def _detect_hardware(self) -> None:
        # 1. Check NVIDIA CUDA
        try:
            import torch
            if torch.cuda.is_available():
                self._device = "cuda"
                self._dtype = "float16"
                self._device_name = torch.cuda.get_device_name(0)
                LOGGER.info("HardwareDeviceManager: Detected NVIDIA CUDA (%s), using FP16 precision.", self._device_name)
                return
        except Exception:
            pass

        # 2. Check Apple Silicon MPS
        try:
            import torch
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._device = "mps"
                self._dtype = "float16"
                self._device_name = "Apple Silicon MPS"
                LOGGER.info("HardwareDeviceManager: Detected Apple Silicon MPS, using FP16 precision.")
                return
        except Exception:
            pass

        # 3. Check Windows DirectML
        try:
            import torch_directml
            self._device = str(torch_directml.device())
            self._dtype = "float16"
            self._device_name = "DirectML GPU"
            LOGGER.info("HardwareDeviceManager: Detected DirectML GPU acceleration.")
            return
        except Exception:
            pass

        # 4. Fallback to CPU
        self._device = "cpu"
        self._dtype = "float32"
        self._device_name = "Host CPU"
        LOGGER.info("HardwareDeviceManager: Running on Host CPU (float32).")

    @property
    def device(self) -> str:
        return self._device

    @property
    def dtype(self) -> str:
        return self._dtype

    @property
    def device_name(self) -> str:
        return self._device_name

    def get_device_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "device": self._device,
            "device_name": self._device_name,
            "dtype": self._dtype,
            "is_gpu": self._device != "cpu",
        }
        if self._device == "cuda":
            try:
                import torch
                total = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                reserved = torch.cuda.memory_reserved(0) / (1024 * 1024)
                info["total_vram_mb"] = round(total, 1)
                info["reserved_vram_mb"] = round(reserved, 1)
            except Exception:
                pass
        return info


def get_hardware_manager() -> HardwareDeviceManager:
    """Global singleton accessor for HardwareDeviceManager."""
    global _GLOBAL_HARDWARE_MANAGER
    if _GLOBAL_HARDWARE_MANAGER is None:
        _GLOBAL_HARDWARE_MANAGER = HardwareDeviceManager()
    return _GLOBAL_HARDWARE_MANAGER
