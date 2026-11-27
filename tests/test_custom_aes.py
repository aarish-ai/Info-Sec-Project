import os
import pytest
from app.core.custom_crypto.aes import (
    CustomAES256,
    aes_256_ctr_encrypt,
    aes_256_ctr_decrypt,
)


def test_aes_256_single_block_known_answer():
    """NIST FIPS 197 Appendix C.3 AES-256 known-answer test vector."""
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    expected_cipher = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")

    cipher = CustomAES256(key)
    assert cipher.encrypt_block(plaintext) == expected_cipher


def test_aes_256_ctr_roundtrip():
    """Verify AES-256-CTR arbitrary-length stream encryption and decryption."""
    key = os.urandom(32)
    nonce = os.urandom(12)
    message = b"MediaGuard Zero-Trust Cryptographic Evidence Asset " * 17 + b"EOF"

    ciphertext = aes_256_ctr_encrypt(key, nonce, message)
    assert len(ciphertext) == len(message)
    assert ciphertext != message

    recovered = aes_256_ctr_decrypt(key, nonce, ciphertext)
    assert recovered == message
