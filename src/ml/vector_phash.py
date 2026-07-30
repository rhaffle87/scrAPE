from __future__ import annotations

import logging
from typing import List
import numpy as np
from PIL import Image

LOGGER = logging.getLogger(__name__)

# Optional PyTorch CUDA hardware acceleration check
HAS_CUDA = False
try:
    import torch
    HAS_CUDA = torch.cuda.is_available()
except ImportError:
    HAS_CUDA = False


class VectorizedPHashCalculator:
    """
    High-throughput perceptual difference hash (dHash) calculator supporting batch
    vectorized NumPy array operations and optional PyTorch CUDA tensor acceleration.
    """

    def __init__(self, use_cuda: bool = True):
        self.use_cuda = use_cuda and HAS_CUDA
        if self.use_cuda:
            LOGGER.info("VectorizedPHashCalculator initialized with PyTorch CUDA acceleration.")
        else:
            LOGGER.info("VectorizedPHashCalculator initialized with NumPy CPU vectorization.")

    def compute_dhash(self, image: Image.Image, hash_size: int = 8) -> int:
        """Compute 64-bit dHash integer for a single PIL image."""
        # Convert image to grayscale and resize to (hash_size + 1, hash_size)
        gray = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
        pixels = np.array(gray, dtype=np.int16)

        # Difference between adjacent pixels along x-axis (rows x hash_size)
        diff = pixels[:, 1:] > pixels[:, :-1]

        # Convert boolean 8x8 matrix to 64-bit integer
        flat_diff = diff.flatten()
        decimal_val = 0
        for i, bit in enumerate(flat_diff):
            if bit:
                decimal_val |= (1 << i)
        return decimal_val

    def compute_dhash_batch(self, images: List[Image.Image], hash_size: int = 8) -> List[int]:
        """Compute dHash integers for a batch of PIL images using matrix vectorization."""
        if not images:
            return []

        # Pre-process all images into grayscale arrays of shape (N, hash_size, hash_size + 1)
        matrix_list = []
        for img in images:
            gray = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
            matrix_list.append(np.array(gray, dtype=np.int16))

        batch_arr = np.stack(matrix_list, axis=0)  # Shape: (N, 8, 9)

        if self.use_cuda:
            try:
                tensor_batch = torch.from_numpy(batch_arr).cuda()
                diff_tensor = tensor_batch[:, :, 1:] > tensor_batch[:, :, :-1]
                diff_batch = diff_tensor.cpu().numpy()
            except Exception as e:
                LOGGER.warning("CUDA execution failed for batch dHash, falling back to NumPy: %s", e)
                diff_batch = batch_arr[:, :, 1:] > batch_arr[:, :, :-1]
        else:
            diff_batch = batch_arr[:, :, 1:] > batch_arr[:, :, :-1]

        # Convert boolean diffs to integers
        results: List[int] = []
        for diff_matrix in diff_batch:
            flat = diff_matrix.flatten()
            val = 0
            for i, b in enumerate(flat):
                if b:
                    val |= (1 << i)
            results.append(val)

        return results

    @staticmethod
    def hamming_distance(hash1: int, hash2: int) -> int:
        """Calculate Hamming distance (number of differing bits) between two 64-bit dHashes."""
        return bin(hash1 ^ hash2).count("1")
