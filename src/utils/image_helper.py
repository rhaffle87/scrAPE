"""Utility functions for inspecting image binary data."""

from __future__ import annotations

import struct
from utils.logger import get_logger

logger = get_logger(__name__)


def get_image_dimensions(data: bytes) -> tuple[int | None, int | None]:
    """Parse image width and height from raw bytes without loading full image.

    Supports PNG, GIF, WebP, and JPEG.
    Returns:
        (width, height) or (None, None) if parsing fails.
    """
    if len(data) < 10:
        return None, None

    # PNG
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        try:
            if len(data) >= 24:
                w, h = struct.unpack(">II", data[16:24])
                return w, h
        except (struct.error, IndexError) as exc:
            logger.debug("Failed to parse PNG dimensions: %s", exc)

    # GIF
    elif data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        try:
            # Logical screen descriptor starts at byte 6
            # width (2 bytes little-endian), height (2 bytes little-endian)
            w, h = struct.unpack("<HH", data[6:10])
            return w, h
        except (struct.error, IndexError) as exc:
            logger.debug("Failed to parse GIF dimensions: %s", exc)

    # WebP
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        try:
            subformat = data[12:16]
            if subformat == b"VP8 ":
                if len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
                    w, h = struct.unpack("<HH", data[26:30])
                    return w & 0x3FFF, h & 0x3FFF
            elif subformat == b"VP8L":
                if len(data) >= 25 and data[20] == 0x2F:
                    val = struct.unpack("<I", data[21:25])[0]
                    w = (val & 0x3FFF) + 1
                    h = ((val >> 14) & 0x3FFF) + 1
                    return w, h
            elif subformat == b"VP8X":
                if len(data) >= 30:
                    w = struct.unpack("<I", data[24:27] + b"\x00")[0] + 1
                    h = struct.unpack("<I", data[27:30] + b"\x00")[0] + 1
                    return w, h
        except (struct.error, IndexError) as exc:
            logger.debug("Failed to parse WebP dimensions: %s", exc)

    # JPEG
    elif data.startswith(b"\xff\xd8"):
        try:
            offset = 2
            while offset < len(data):
                if data[offset] == 0xFF:
                    while offset < len(data) and data[offset] == 0xFF:
                        offset += 1
                    if offset >= len(data):
                        break
                    marker = data[offset]
                    offset += 1
                    if marker in (
                        0x00,
                        0x01,
                        0xD0,
                        0xD1,
                        0xD2,
                        0xD3,
                        0xD4,
                        0xD5,
                        0xD6,
                        0xD7,
                        0xD8,
                        0xD9,
                    ):
                        continue
                    if (
                        (0xC0 <= marker <= 0xC3)
                        or (0xC5 <= marker <= 0xC7)
                        or (0xC9 <= marker <= 0xCB)
                        or (0xCD <= marker <= 0xCF)
                    ):
                        if offset + 7 <= len(data):
                            # skip length (2 bytes), precision (1 byte)
                            h, w = struct.unpack(">HH", data[offset + 3 : offset + 7])
                            return w, h
                        break
                    else:
                        if offset + 2 <= len(data):
                            length = struct.unpack(">H", data[offset : offset + 2])[0]
                            offset += length
                        else:
                            break
                else:
                    offset += 1
        except (struct.error, IndexError) as exc:
            logger.debug("Failed to parse JPEG dimensions: %s", exc)

    return None, None


def compute_dhash(image_bytes: bytes, hash_size: int = 8) -> int | None:
    """Compute a 64-bit difference hash (dHash) for raw image bytes.

    Returns:
        64-bit integer hash or None if hashing fails.
    """
    try:
        from io import BytesIO
        from PIL import Image

        img = Image.open(BytesIO(image_bytes)).convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())

        difference = []
        for row in range(hash_size):
            for col in range(hash_size):
                pixel_left = pixels[row * (hash_size + 1) + col]
                pixel_right = pixels[row * (hash_size + 1) + col + 1]
                difference.append(pixel_left > pixel_right)

        decimal_value = 0
        for index, value in enumerate(difference):
            if value:
                decimal_value += 1 << index

        return decimal_value
    except Exception as exc:
        logger.debug("Failed to compute dHash: %s", exc)
        return None


def hamming_distance(hash1: int, hash2: int) -> int:
    """Calculate the Hamming distance (number of differing bits) between two 64-bit hashes."""
    return bin(hash1 ^ hash2).count("1")

