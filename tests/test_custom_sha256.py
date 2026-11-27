import pytest
from app.core.custom_crypto.sha256 import CustomSHA256


def test_custom_sha256_empty_string():
    """NIST FIPS 180-4 test vector for empty input."""
    h = CustomSHA256()
    assert h.hexdigest() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_custom_sha256_standard_vector():
    """NIST FIPS 180-4 test vector for 'abc'."""
    h = CustomSHA256(b"abc")
    assert h.hexdigest() == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_custom_sha256_streaming_chunks():
    """Test incremental streaming chunks and multi-block padding."""
    msg = b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"
    h1 = CustomSHA256()
    for i in range(0, len(msg), 7):
        h1.update(msg[i:i + 7])
    assert h1.hexdigest() == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"
    # Verify hexdigest() is non-destructive and digest() returns 32 raw bytes
    assert len(h1.digest()) == 32
    assert h1.digest().hex() == h1.hexdigest()
