import io
import hashlib
import pytest
from PIL import Image
from app.core.hashing import (
    compute_streamed_sha256,
    compute_phash,
    compute_phash_distance,
)

def test_compute_streamed_sha256_filepath(tmp_path):
    """Verify SHA-256 computed on a file path matches hashlib standard output."""
    test_data = b"MediaGuard Integrity Test Vector 12345"
    test_file = tmp_path / "sample.bin"
    test_file.write_bytes(test_data)
    
    expected_hash = hashlib.sha256(test_data).hexdigest()
    computed_hash = compute_streamed_sha256(test_file)
    
    assert computed_hash == expected_hash
    assert len(computed_hash) == 64

def test_compute_streamed_sha256_stream():
    """Verify SHA-256 computed on an in-memory BytesIO stream matches hashlib."""
    test_data = b"In-memory stream test payload for SHA-256"
    stream = io.BytesIO(test_data)
    
    expected_hash = hashlib.sha256(test_data).hexdigest()
    computed_hash = compute_streamed_sha256(stream)
    
    assert computed_hash == expected_hash

def test_compute_streamed_sha256_chunking(tmp_path):
    """Verify multi-chunk streamed processing on data exceeding 64KB chunk size."""
    # 200KB of repeated pseudo-random pattern
    chunk_pattern = b"0123456789ABCDEF" * 1024  # 16KB
    large_data = chunk_pattern * 13              # 208KB
    large_file = tmp_path / "large.dat"
    large_file.write_bytes(large_data)
    
    expected_hash = hashlib.sha256(large_data).hexdigest()
    computed_hash = compute_streamed_sha256(large_file, chunk_size=65536)
    
    assert computed_hash == expected_hash

def test_compute_phash_valid_image():
    """Verify pHash produces consistent 16-character hex strings for images."""
    img = Image.new('RGB', (120, 120), color='navy')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    phash = compute_phash(buf)
    assert phash != "N/A"
    assert len(phash) == 16
    # Verify it can be parsed as hex
    int(phash, 16)

def test_compute_phash_non_image():
    """Verify pHash gracefully returns 'N/A' for binary/video non-image streams."""
    non_image_stream = io.BytesIO(b"\x00\x01\x02\x03\x04\x05non-image-data")
    result = compute_phash(non_image_stream)
    assert result == "N/A"

def test_compute_phash_distance():
    """Verify Hamming distance calculation between pHash values."""
    img1 = Image.new('RGB', (100, 100), color='white')
    buf1 = io.BytesIO()
    img1.save(buf1, format='PNG')
    buf1.seek(0)
    hash1 = compute_phash(buf1)

    # Identical image -> distance 0
    assert compute_phash_distance(hash1, hash1) == 0

    # Slightly modified image (black dot)
    img2 = Image.new('RGB', (100, 100), color='white')
    img2.putpixel((50, 50), (0, 0, 0))
    buf2 = io.BytesIO()
    img2.save(buf2, format='PNG')
    buf2.seek(0)
    hash2 = compute_phash(buf2)

    dist = compute_phash_distance(hash1, hash2)
    assert dist >= 0

    # Handling 'N/A'
    assert compute_phash_distance("N/A", hash1) == -1
    assert compute_phash_distance(hash1, "N/A") == -1
    assert compute_phash_distance("invalid", hash1) == -1
