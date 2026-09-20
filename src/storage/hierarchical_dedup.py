"""Hierarchical Multi-Tier Deduplication Engine (L1 SHA-256 Bloom, L2 pHash/dHash, L3 Vector Similarity)."""

from __future__ import annotations

import logging
import math
import threading
from typing import Any

from storage.bloom_filter import BloomFilter

LOGGER = logging.getLogger(__name__)


def hamming_distance(h1: int, h2: int) -> int:
    """Compute bitwise Hamming distance between two 64-bit integer hashes."""
    return bin(h1 ^ h2).count("1")


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two normalized or unnormalized float vectors."""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class BKNode:
    """Node in a BK-tree for discrete metric space search."""
    __slots__ = ("hash_val", "identifier", "children")

    def __init__(self, hash_val: int, identifier: str):
        self.hash_val = hash_val
        self.identifier = identifier
        self.children: dict[int, BKNode] = {}


class BKTree:
    """BK-tree for fast sub-linear perceptual hash indexing."""

    def __init__(self):
        self.root: BKNode | None = None
        self._size = 0
        self._lock = threading.RLock()

    def add(self, hash_val: int, identifier: str) -> None:
        with self._lock:
            if self.root is None:
                self.root = BKNode(hash_val, identifier)
                self._size = 1
                return

            curr = self.root
            while True:
                dist = hamming_distance(hash_val, curr.hash_val)
                if dist == 0:
                    return  # Exact match already present
                if dist not in curr.children:
                    curr.children[dist] = BKNode(hash_val, identifier)
                    self._size += 1
                    break
                curr = curr.children[dist]

    def find_nearest(self, hash_val: int, max_dist: int = 4) -> tuple[int, str] | None:
        """Find nearest item within max_dist. Returns (distance, identifier) or None."""
        with self._lock:
            if self.root is None:
                return None

            best_match: tuple[int, str] | None = None
            best_dist = max_dist + 1

            candidates = [self.root]
            while candidates:
                node = candidates.pop()
                dist = hamming_distance(hash_val, node.hash_val)
                if dist <= max_dist and dist < best_dist:
                    best_dist = dist
                    best_match = (dist, node.identifier)
                    if dist == 0:
                        return best_match

                # BK-tree property: search child branches in range [dist - max_dist, dist + max_dist]
                low = dist - max_dist
                high = dist + max_dist
                for d, child in node.children.items():
                    if low <= d <= high:
                        candidates.append(child)

            return best_match

    def __len__(self) -> int:
        return self._size


class HierarchicalDedupEngine:
    """
    Three-tier hierarchical deduplication engine:
      L1: In-memory SHA-256 Bloom filter for 0.01ms exact-match byte deduplication.
      L2: Perceptual dHash/pHash indexed in a BK-tree (Hamming distance <= threshold).
      L3: Semantic vector cosine similarity check for deep visual deduplication.
    """

    def __init__(
        self,
        capacity: int = 500_000,
        hamming_threshold: int = 4,
        similarity_threshold: float = 0.96,
    ):
        self.hamming_threshold = hamming_threshold
        self.similarity_threshold = similarity_threshold

        # L1: Bloom filter for exact SHA-256 byte hashes
        self.l1_bloom = BloomFilter(capacity=capacity, error_rate=0.001)
        self._l1_exact_set: set[str] = set()  # Confirms false-positives

        # L2: BK-Tree for perceptual hashes
        self.l2_bktree = BKTree()

        # L3: Embedding vectors
        self.l3_embeddings: list[tuple[list[float], str]] = []

        self._lock = threading.RLock()

    def check_duplicate(
        self,
        sha256: str | None = None,
        phash: int | str | None = None,
        embedding: list[float] | None = None,
    ) -> tuple[bool, str, str]:
        """
        Check if asset is duplicate across L1 -> L2 -> L3.
        Returns (is_duplicate, reason, matched_id).
        """
        with self._lock:
            # L1: Exact byte match
            if sha256:
                norm_sha = sha256.lower().strip()
                if norm_sha in self.l1_bloom:
                    if norm_sha in self._l1_exact_set:
                        return True, "exact_sha256_match", norm_sha

            # L2: Perceptual hash match
            if phash is not None:
                int_hash = int(phash, 16) if isinstance(phash, str) else int(phash)
                match = self.l2_bktree.find_nearest(int_hash, max_dist=self.hamming_threshold)
                if match:
                    dist, matched_id = match
                    return True, f"phash_hamming_distance_{dist}", matched_id

            # L3: Semantic embedding cosine match
            if embedding and self.l3_embeddings:
                for stored_vec, stored_id in self.l3_embeddings:
                    sim = cosine_similarity(embedding, stored_vec)
                    if sim >= self.similarity_threshold:
                        return True, f"vector_cosine_similarity_{sim:.3f}", stored_id

            return False, "", ""

    def record_asset(
        self,
        sha256: str,
        phash: int | str | None = None,
        embedding: list[float] | None = None,
        identifier: str = "",
    ) -> None:
        """Register newly verified asset into L1, L2, and L3 indices."""
        with self._lock:
            if sha256:
                norm_sha = sha256.lower().strip()
                self.l1_bloom.add(norm_sha)
                self._l1_exact_set.add(norm_sha)

            if phash is not None:
                int_hash = int(phash, 16) if isinstance(phash, str) else int(phash)
                self.l2_bktree.add(int_hash, identifier or sha256)

            if embedding:
                self.l3_embeddings.append((embedding, identifier or sha256))

    def stats(self) -> dict[str, Any]:
        """Return index counts across all 3 tiers."""
        with self._lock:
            return {
                "l1_exact_sha256_count": len(self._l1_exact_set),
                "l2_phash_bktree_size": len(self.l2_bktree),
                "l3_embeddings_count": len(self.l3_embeddings),
            }
