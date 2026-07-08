"""Utility functions for inspecting image binary data."""

from __future__ import annotations

import struct


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
        except Exception:
            pass

    # GIF
    elif data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        try:
            # Logical screen descriptor starts at byte 6
            # width (2 bytes little-endian), height (2 bytes little-endian)
            w, h = struct.unpack("<HH", data[6:10])
            return w, h
        except Exception:
            pass

    # WebP
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        try:
            subformat = data[12:16]
            if subformat == b"VP8 ":
                if len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
                    w, h = struct.unpack("<HH", data[26:30])
                    return w & 0x3fff, h & 0x3fff
            elif subformat == b"VP8L":
                if len(data) >= 25 and data[20] == 0x2f:
                    val = struct.unpack("<I", data[21:25])[0]
                    w = (val & 0x3fff) + 1
                    h = ((val >> 14) & 0x3fff) + 1
                    return w, h
            elif subformat == b"VP8X":
                if len(data) >= 30:
                    w = struct.unpack("<I", data[24:27] + b"\x00")[0] + 1
                    h = struct.unpack("<I", data[27:30] + b"\x00")[0] + 1
                    return w, h
        except Exception:
            pass

    # JPEG
    elif data.startswith(b"\xff\xd8"):
        try:
            offset = 2
            while offset < len(data):
                if data[offset] == 0xff:
                    while offset < len(data) and data[offset] == 0xff:
                        offset += 1
                    if offset >= len(data):
                        break
                    marker = data[offset]
                    offset += 1
                    if marker in (0x00, 0x01, 0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0xd8, 0xd9):
                        continue
                    if (0xc0 <= marker <= 0xc3) or (0xc5 <= marker <= 0xc7) or (0xc9 <= marker <= 0xcb) or (0xcd <= marker <= 0xcf):
                        if offset + 7 <= len(data):
                            # skip length (2 bytes), precision (1 byte)
                            h, w = struct.unpack(">HH", data[offset+3:offset+7])
                            return w, h
                        break
                    else:
                        if offset + 2 <= len(data):
                            length = struct.unpack(">H", data[offset:offset+2])[0]
                            offset += length
                        else:
                            break
                else:
                    offset += 1
        except Exception:
            pass

    return None, None
