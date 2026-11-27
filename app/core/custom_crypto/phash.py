"""Pure-Python 2D-DCT Perceptual Hashing (pHash) and Hamming distance engine."""
import math
from typing import List
from PIL import Image

_N = 32
_HASH_SIZE = 8

# Precompute 1D DCT-II basis matrix for N=32
_COS_TABLE: List[List[float]] = [
    [
        math.cos(((2 * x + 1) * u * math.pi) / (2 * _N))
        for x in range(_N)
    ]
    for u in range(_N)
]

_ALPHA: List[float] = [
    math.sqrt(1.0 / _N) if u == 0 else math.sqrt(2.0 / _N)
    for u in range(_N)
]


def _dct_1d(signal: List[float]) -> List[float]:
    return [
        _ALPHA[u] * sum(signal[x] * _COS_TABLE[u][x] for x in range(_N))
        for u in range(_N)
    ]


def custom_dct_phash(img: Image.Image) -> str:
    """
    Computes a 64-bit (16-hex-char) 2D-DCT perceptual hash for an image
    in pure Python without using the `imagehash` library.
    """
    resample_filter = getattr(Image, "Resampling", Image).LANCZOS
    gray = img.convert("L").resize((_N, _N), resample_filter)
    raw = list(gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata())
    matrix: List[List[float]] = [
        [float(raw[r * _N + c]) for c in range(_N)]
        for r in range(_N)
    ]

    # Separable 2D DCT: 1D DCT on rows, then 1D DCT on top 8 columns
    row_dct = [_dct_1d(row) for row in matrix]
    low_freq: List[float] = []
    for u in range(_HASH_SIZE):
        for v in range(_HASH_SIZE):
            col_val = _ALPHA[u] * sum(
                row_dct[y][v] * _COS_TABLE[u][y] for y in range(_N)
            )
            low_freq.append(col_val)

    # Median over the 63 AC coefficients (excluding DC at index 0) or all 64
    ac_sorted = sorted(low_freq[1:])
    median = ac_sorted[len(ac_sorted) // 2]

    bits = 0
    for val in low_freq:
        bits = (bits << 1) | (1 if val > median else 0)

    return f"{bits:016x}"


def custom_hamming_distance(hash1_hex: str, hash2_hex: str) -> int:
    """Computes Hamming distance between two 16-character hex perceptual hashes."""
    if not hash1_hex or not hash2_hex:
        return -1

    clean1 = hash1_hex.strip().lower()
    clean2 = hash2_hex.strip().lower()
    if clean1 == "n/a" or clean2 == "n/a":
        return -1

    try:
        val1 = int(clean1, 16)
        val2 = int(clean2, 16)
        return bin(val1 ^ val2).count("1")
    except (ValueError, TypeError):
        return -1
