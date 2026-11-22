import pytest
from cryptography.exceptions import InvalidTag
from app.core.key_management import generate_user_key_pairs
from app.core.ciphers import (
    encrypt_media_envelope,
    decrypt_media_envelope,
)

def test_envelope_encrypt_decrypt_roundtrip():
    """Verify full AES-256-GCM envelope encryption and RSA-OAEP unwrapping roundtrip."""
    keys = generate_user_key_pairs(key_size=2048)
    original_media = b"\x89PNG\r\n\x1a\n" + (b"BINARY_MEDIA_PAYLOAD_TEST_1234567890" * 50)

    envelope = encrypt_media_envelope(original_media, keys['encryption_public_pem'])

    assert 'ciphertext' in envelope
    assert 'wrapped_aes_key' in envelope
    assert 'nonce' in envelope
    assert 'auth_tag' in envelope

    assert len(envelope['nonce']) == 12
    assert len(envelope['auth_tag']) == 16
    assert envelope['ciphertext'] != original_media

    decrypted_media = decrypt_media_envelope(
        ciphertext=envelope['ciphertext'],
        wrapped_aes_key=envelope['wrapped_aes_key'],
        nonce=envelope['nonce'],
        auth_tag=envelope['auth_tag'],
        owner_private_enc_key_pem=keys['encryption_private_pem']
    )

    assert decrypted_media == original_media

def test_auth_tag_tampering_raises_invalid_tag():
    """Verify that tampering with the authentication tag causes AES-GCM to reject decryption."""
    keys = generate_user_key_pairs(key_size=2048)
    original_media = b"Sensitive Confidential Image Bytes"
    envelope = encrypt_media_envelope(original_media, keys['encryption_public_pem'])

    corrupted_tag = bytearray(envelope['auth_tag'])
    corrupted_tag[0] ^= 0xFF

    with pytest.raises(InvalidTag):
        decrypt_media_envelope(
            ciphertext=envelope['ciphertext'],
            wrapped_aes_key=envelope['wrapped_aes_key'],
            nonce=envelope['nonce'],
            auth_tag=bytes(corrupted_tag),
            owner_private_enc_key_pem=keys['encryption_private_pem']
        )

def test_ciphertext_tampering_raises_invalid_tag():
    """Verify that tampering with ciphertext causes authenticated decryption rejection."""
    keys = generate_user_key_pairs(key_size=2048)
    original_media = b"Sensitive Confidential Video Bytes"
    envelope = encrypt_media_envelope(original_media, keys['encryption_public_pem'])

    corrupted_ct = bytearray(envelope['ciphertext'])
    corrupted_ct[0] ^= 0xFF

    with pytest.raises(InvalidTag):
        decrypt_media_envelope(
            ciphertext=bytes(corrupted_ct),
            wrapped_aes_key=envelope['wrapped_aes_key'],
            nonce=envelope['nonce'],
            auth_tag=envelope['auth_tag'],
            owner_private_enc_key_pem=keys['encryption_private_pem']
        )

def test_nonce_tampering_raises_invalid_tag():
    """Verify that tampering with the nonce causes authenticated decryption failure."""
    keys = generate_user_key_pairs(key_size=2048)
    original_media = b"Authentic Media Buffer"
    envelope = encrypt_media_envelope(original_media, keys['encryption_public_pem'])

    corrupted_nonce = bytearray(envelope['nonce'])
    corrupted_nonce[0] ^= 0xFF

    with pytest.raises(InvalidTag):
        decrypt_media_envelope(
            ciphertext=envelope['ciphertext'],
            wrapped_aes_key=envelope['wrapped_aes_key'],
            nonce=bytes(corrupted_nonce),
            auth_tag=envelope['auth_tag'],
            owner_private_enc_key_pem=keys['encryption_private_pem']
        )

def test_wrong_private_key_unwrap_failure():
    """Verify that attempting to unwrap AES key with a different user's private key fails."""
    user1_keys = generate_user_key_pairs(key_size=2048)
    user2_keys = generate_user_key_pairs(key_size=2048)

    original_media = b"Secret Media of User 1"
    envelope = encrypt_media_envelope(original_media, user1_keys['encryption_public_pem'])

    # Attempting to decrypt User 1's envelope using User 2's private key
    with pytest.raises(ValueError):
        decrypt_media_envelope(
            ciphertext=envelope['ciphertext'],
            wrapped_aes_key=envelope['wrapped_aes_key'],
            nonce=envelope['nonce'],
            auth_tag=envelope['auth_tag'],
            owner_private_enc_key_pem=user2_keys['encryption_private_pem']
        )

def test_nonce_and_key_freshness():
    """Verify that every envelope encryption generates a fresh AES key and nonce."""
    keys = generate_user_key_pairs(key_size=2048)
    media = b"Repeated Media Payload"

    env1 = encrypt_media_envelope(media, keys['encryption_public_pem'])
    env2 = encrypt_media_envelope(media, keys['encryption_public_pem'])

    assert env1['nonce'] != env2['nonce']
    assert env1['wrapped_aes_key'] != env2['wrapped_aes_key']
    assert env1['ciphertext'] != env2['ciphertext']
