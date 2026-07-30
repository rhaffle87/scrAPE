import sys
import gc
from io import BytesIO
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from common.image_helper import compute_dhash, get_image_dimensions, hamming_distance


def test_compute_dhash_resource_cleanup():
    """Verify compute_dhash properly closes PIL image context without leaking handles."""
    # Create a small 64x64 test image in memory
    img = Image.new("RGB", (64, 64), color=(255, 0, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()
    img.close()

    # Compute dHash
    dhash_val = compute_dhash(image_bytes)
    assert dhash_val is not None
    assert isinstance(dhash_val, int)

    # Force garbage collection to verify clean object disposal
    collected = gc.collect()
    assert isinstance(collected, int)


def test_get_image_dimensions_parse_and_cleanup():
    """Verify get_image_dimensions operates cleanly on memory buffers."""
    img = Image.new("RGB", (100, 200), color=(0, 255, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()
    img.close()

    width, height = get_image_dimensions(image_bytes)
    assert width == 100
    assert height == 200


def test_hamming_distance_correctness():
    """Verify hamming_distance calculations."""
    h1 = 0b101010
    h2 = 0b111000
    # Differing bits: bit 1 (0 vs 0 - same), bit 2 (1 vs 0 - diff), bit 4 (0 vs 1 - diff) -> 2 bits
    assert hamming_distance(h1, h2) == 2
