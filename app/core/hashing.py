import io
import hashlib
from pathlib import Path
from typing import Union
from PIL import Image
import imagehash

DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 KB

def compute_streamed_sha256(
    file_path_or_stream: Union[str, Path, io.BufferedIOBase, io.RawIOBase, io.BytesIO],
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> str:
    """
    Computes SHA-256 hash using streaming chunks to minimize memory consumption.
    Accepts a filesystem path (str or Path) or a binary readable stream.
    If a seekable stream is provided, its original position is restored.
    """
    hasher = hashlib.sha256()

    if isinstance(file_path_or_stream, (str, Path)):
        with open(file_path_or_stream, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
    else:
        stream = file_path_or_stream
        initial_pos = None
        if hasattr(stream, 'seekable') and stream.seekable():
            try:
                initial_pos = stream.tell()
            except (OSError, io.UnsupportedOperation):
                initial_pos = None

        try:
            while chunk := stream.read(chunk_size):
                hasher.update(chunk)
        finally:
            if initial_pos is not None:
                try:
                    stream.seek(initial_pos)
                except (OSError, io.UnsupportedOperation):
                    pass

    return hasher.hexdigest().lower()

def compute_phash(
    file_path_or_stream: Union[str, Path, io.BufferedIOBase, io.RawIOBase, io.BytesIO]
) -> str:
    """
    Computes the DCT perceptual hash (pHash) for an image.
    Returns 16-character hexadecimal string.
    Returns 'N/A' for non-image files, videos, or corrupted streams.
    """
    initial_pos = None
    if not isinstance(file_path_or_stream, (str, Path)):
        stream = file_path_or_stream
        if hasattr(stream, 'seekable') and stream.seekable():
            try:
                initial_pos = stream.tell()
            except (OSError, io.UnsupportedOperation):
                initial_pos = None

    try:
        # Open and load image to verify decodability
        with Image.open(file_path_or_stream) as img:
            phash_obj = imagehash.phash(img)
            return str(phash_obj).lower()
    except Exception:
        return "N/A"
    finally:
        if initial_pos is not None and not isinstance(file_path_or_stream, (str, Path)):
            try:
                file_path_or_stream.seek(initial_pos)
            except (OSError, io.UnsupportedOperation):
                pass

def compute_phash_distance(hash1_hex: str, hash2_hex: str) -> int:
    """
    Computes the Hamming distance between two hexadecimal perceptual hashes.
    Returns -1 if either hash is 'N/A', empty, or not a valid hex string.
    A distance of 0 means identical visual perception.
    Distance <= 10 typically indicates perceptual similarity.
    """
    if not hash1_hex or not hash2_hex:
        return -1
    
    clean1 = hash1_hex.strip().lower()
    clean2 = hash2_hex.strip().lower()

    if clean1 == 'n/a' or clean2 == 'n/a':
        return -1

    try:
        val1 = int(clean1, 16)
        val2 = int(clean2, 16)
        # Compute Hamming distance via XOR and bit count
        return bin(val1 ^ val2).count('1')
    except (ValueError, TypeError):
        return -1
