import os
import pytest
from cryptography.exceptions import InvalidTag
from app.core.key_management import (
    generate_user_key_pairs,
    derive_kek,
    encrypt_private_key,
    decrypt_private_key,
    generate_salt,
)

def test_key_separation_and_generation():
    """Verify that dual RSA key pairs are generated with strict separation."""
    keys = generate_user_key_pairs(key_size=2048)
    
    assert 'signing_private_pem' in keys
    assert 'signing_public_pem' in keys
    assert 'encryption_private_pem' in keys
    assert 'encryption_public_pem' in keys

    # Verify signing keys differ from encryption keys (strict separation)
    assert keys['signing_private_pem'] != keys['encryption_private_pem']
    assert keys['signing_public_pem'] != keys['encryption_public_pem']

    # Verify PEM structure
    assert keys['signing_private_pem'].startswith(b'-----BEGIN PRIVATE KEY-----')
    assert keys['signing_public_pem'].startswith(b'-----BEGIN PUBLIC KEY-----')
    assert keys['encryption_private_pem'].startswith(b'-----BEGIN PRIVATE KEY-----')
    assert keys['encryption_public_pem'].startswith(b'-----BEGIN PUBLIC KEY-----')

def test_scrypt_kek_derivation():
    """Verify scrypt KDF produces 32-byte keys deterministically."""
    password = "SuperSecretSecurePassword!123"
    salt = generate_salt(16)
    
    assert len(salt) == 16

    kek1 = derive_kek(password, salt)
    kek2 = derive_kek(password, salt)

    assert len(kek1) == 32
    assert kek1 == kek2

    # Different salt produces different KEK
    different_salt = generate_salt(16)
    kek3 = derive_kek(password, different_salt)
    assert kek1 != kek3

    # Different password produces different KEK
    kek4 = derive_kek("DifferentPassword!123", salt)
    assert kek1 != kek4

def test_private_key_encryption_roundtrip():
    """Verify AES-256-GCM encryption and decryption roundtrip of private PEM."""
    keys = generate_user_key_pairs(key_size=2048)
    private_pem = keys['signing_private_pem']
    kek = derive_kek("MasterPassword#456", generate_salt(16))

    ciphertext, nonce, tag = encrypt_private_key(private_pem, kek)
    
    assert len(nonce) == 12
    assert len(tag) == 16
    assert ciphertext != private_pem

    decrypted_pem = decrypt_private_key(ciphertext, nonce, tag, kek)
    assert decrypted_pem == private_pem

def test_private_key_encryption_tamper_detection():
    """Verify that tampering with ciphertext, tag, or using the wrong KEK raises InvalidTag."""
    keys = generate_user_key_pairs(key_size=2048)
    private_pem = keys['encryption_private_pem']
    kek1 = derive_kek("PasswordOne#1", generate_salt(16))
    kek2 = derive_kek("PasswordTwo#2", generate_salt(16))

    ciphertext, nonce, tag = encrypt_private_key(private_pem, kek1)

    # 1. Corrupted ciphertext
    tampered_ciphertext = bytearray(ciphertext)
    tampered_ciphertext[0] ^= 0xFF
    with pytest.raises(InvalidTag):
        decrypt_private_key(bytes(tampered_ciphertext), nonce, tag, kek1)

    # 2. Corrupted tag
    tampered_tag = bytearray(tag)
    tampered_tag[0] ^= 0xFF
    with pytest.raises(InvalidTag):
        decrypt_private_key(ciphertext, nonce, bytes(tampered_tag), kek1)

    # 3. Wrong KEK
    with pytest.raises(InvalidTag):
        decrypt_private_key(ciphertext, nonce, tag, kek2)

def test_private_key_nonce_freshness():
    """Verify that encrypting the same private PEM twice yields distinct nonces and ciphertexts."""
    keys = generate_user_key_pairs(key_size=2048)
    private_pem = keys['signing_private_pem']
    kek = derive_kek("MyPassword!123", generate_salt(16))

    ct1, nonce1, tag1 = encrypt_private_key(private_pem, kek)
    ct2, nonce2, tag2 = encrypt_private_key(private_pem, kek)

    assert nonce1 != nonce2
    assert ct1 != ct2
