"""Zero-dependency pure-Python Bitmask Bloom Filter for high-throughput URL deduplication."""

from __future__ import annotations

import hashlib
import math
import threading
from typing import Iterable, Optional


class BloomFilter:
    """Thread-safe, zero-dependency Bloom filter using Python integers as bit arrays
    and Kirsch-Mitzenmacher dual-hashing (h1 + i * h2 mod m).
    """

    def __init__(
        self,
        capacity: int = 1_000_000,
        error_rate: float = 0.01,
    ):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0")
        if not (0 < error_rate < 1):
            raise ValueError("Error rate must be between 0 and 1")

        self.capacity = capacity
        self.error_rate = error_rate

        # Calculate optimal bit size (m) and number of hash functions (k)
        # m = - (n * ln(p)) / (ln(2)^2)
        # k = (m / n) * ln(2)
        num_bits = -1 * (capacity * math.log(error_rate)) / (math.log(2) ** 2)
        self.size: int = int(math.ceil(num_bits))
        self.num_hashes: int = max(1, int(math.ceil((self.size / capacity) * math.log(2))))

        self._bits: int = 0
        self._count: int = 0
        self._lock = threading.Lock()

    def _hashes(self, item: str) -> Iterable[int]:
        """Generate k hash positions using Kirsch-Mitzenmacher technique:
        g_i(x) = (h1(x) + i * h2(x)) % size
        """
        encoded = item.encode("utf-8", errors="replace")
        # Use 16-byte blake2b digest to extract two 64-bit independent hashes h1 and h2
        digest = hashlib.blake2b(encoded, digest_size=16).digest()
        h1 = int.from_bytes(digest[:8], byteorder="big", signed=False)
        h2 = int.from_bytes(digest[8:], byteorder="big", signed=False)

        # In case h2 is 0, provide non-zero step
        if h2 == 0:
            h2 = 1

        size = self.size
        for i in range(self.num_hashes):
            yield (h1 + i * h2) % size

    def add(self, item: str) -> None:
        """Add an item to the Bloom filter."""
        with self._lock:
            for bit_pos in self._hashes(item):
                self._bits |= 1 << bit_pos
            self._count += 1

    def contains(self, item: str) -> bool:
        """Check if an item might be in the Bloom filter.
        Returns False: Guaranteed NOT in the set.
        Returns True: MIGHT be in the set (with false positive rate <= error_rate).
        """
        with self._lock:
            bits = self._bits
            for bit_pos in self._hashes(item):
                if not (bits & (1 << bit_pos)):
                    return False
            return True

    def __contains__(self, item: str) -> bool:
        return self.contains(item)

    def count(self) -> int:
        """Return the number of elements added."""
        with self._lock:
            return self._count

    def clear(self) -> None:
        """Reset the Bloom filter."""
        with self._lock:
            self._bits = 0
            self._count = 0

    def to_bytes(self) -> bytes:
        """Export the bit array to bytes."""
        with self._lock:
            length = (self.size + 7) // 8
            return self._bits.to_bytes(length, byteorder="big")

    def from_bytes(self, data: bytes, count: Optional[int] = None) -> None:
        """Load bit array from bytes."""
        with self._lock:
            self._bits = int.from_bytes(data, byteorder="big")
            if count is not None:
                self._count = count
            else:
                self._count = 0
