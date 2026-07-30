from __future__ import annotations

from unittest.mock import patch, MagicMock
from PIL import Image
from src.monitoring.hardware_governor import HardwareLoadGovernor
from src.ml.vector_phash import VectorizedPHashCalculator


def test_hardware_governor_normal_load(tmp_path):
    gov = HardwareLoadGovernor(config_path=tmp_path / "domain_config.json")
    with patch("psutil.cpu_percent", return_value=30.0), \
         patch("psutil.virtual_memory") as mock_mem:
        mock_mem_obj = MagicMock()
        mock_mem_obj.available = 80.0
        mock_mem_obj.total = 100.0
        mock_mem.return_value = mock_mem_obj

        metrics = gov.get_metrics()
        assert metrics["cpu_percent"] == 30.0
        assert metrics["ram_percent_available"] == 80.0

        scale = gov.get_concurrency_scale_factor()
        assert scale == 1.0


def test_hardware_governor_high_and_critical_load(tmp_path):
    gov = HardwareLoadGovernor(config_path=tmp_path / "domain_config.json", max_cpu_percent=85.0, min_ram_percent=15.0)

    # High load (CPU 88%) -> 0.50x
    with patch("psutil.cpu_percent", return_value=88.0), \
         patch("psutil.virtual_memory") as mock_mem:
        mock_mem_obj = MagicMock()
        mock_mem_obj.available = 50.0
        mock_mem_obj.total = 100.0
        mock_mem.return_value = mock_mem_obj

        gov._last_poll_time = 0.0  # force poll
        assert gov.get_concurrency_scale_factor() == 0.50

    # Critical load (CPU 96%) -> 0.25x
    with patch("psutil.cpu_percent", return_value=96.0), \
         patch("psutil.virtual_memory") as mock_mem:
        mock_mem_obj = MagicMock()
        mock_mem_obj.available = 50.0
        mock_mem_obj.total = 100.0
        mock_mem.return_value = mock_mem_obj

        gov._last_poll_time = 0.0  # force poll
        assert gov.get_concurrency_scale_factor() == 0.25


def test_vectorized_phash_calculator_single_and_batch():
    calc = VectorizedPHashCalculator(use_cuda=False)

    img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img2 = Image.new("RGB", (100, 100), color=(0, 255, 0))

    h1_single = calc.compute_dhash(img1)
    h2_single = calc.compute_dhash(img2)

    batch_hashes = calc.compute_dhash_batch([img1, img2])
    assert len(batch_hashes) == 2
    assert batch_hashes[0] == h1_single
    assert batch_hashes[1] == h2_single


def test_vectorized_phash_hamming_distance():
    calc = VectorizedPHashCalculator(use_cuda=False)
    img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))

    h1 = calc.compute_dhash(img1)
    dist_self = calc.hamming_distance(h1, h1)
    assert dist_self == 0
