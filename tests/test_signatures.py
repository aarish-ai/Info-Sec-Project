import json
import pytest
from app.core.key_management import generate_user_key_pairs
from app.core.signatures import (
    build_canonical_manifest,
    sign_manifest,
    verify_manifest_signature,
)

def test_canonical_manifest_determinism():
    """Verify that build_canonical_manifest generates deterministic, sorted, compact JSON."""
    manifest1 = build_canonical_manifest(
        media_id="media-uuid-001",
        owner_id=42,
        filename="photo.jpg",
        file_size=204800,
        mime_type="image/jpeg",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        phash="d41d8cd98f00b204",
        timestamp_utc="2026-11-22T12:00:00Z"
    )

    manifest2 = build_canonical_manifest(
        timestamp_utc="2026-11-22T12:00:00Z",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        phash="d41d8cd98f00b204",
        mime_type="image/jpeg",
        file_size=204800,
        filename="photo.jpg",
        owner_id=42,
        media_id="media-uuid-001"
    )

    assert manifest1 == manifest2
    # Verify compact formatting (no space after colon or comma)
    assert ": " not in manifest1
    assert ", " not in manifest1

    # Verify keys are alphabetically sorted
    data = json.loads(manifest1)
    keys = list(data.keys())
    assert keys == sorted(keys)

def test_sign_and_verify_manifest_valid():
    """Verify RSA-PSS signature creation and successful verification."""
    keys = generate_user_key_pairs(key_size=2048)
    manifest = build_canonical_manifest(
        media_id="test-media-123",
        owner_id=1,
        filename="sample.png",
        file_size=1024,
        mime_type="image/png",
        sha256_hash="abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
        phash="1122334455667788",
        timestamp_utc="2026-11-22T15:00:00Z"
    )

    signature = sign_manifest(manifest, keys['signing_private_pem'])
    assert isinstance(signature, bytes)
    assert len(signature) > 0

    is_valid = verify_manifest_signature(
        manifest,
        signature,
        keys['signing_public_pem']
    )
    assert is_valid is True

def test_tamper_detection_in_manifest():
    """Verify that any tampering with the canonical manifest invalidates the signature."""
    keys = generate_user_key_pairs(key_size=2048)
    manifest = build_canonical_manifest(
        media_id="test-media-123",
        owner_id=1,
        filename="sample.png",
        file_size=1024,
        mime_type="image/png",
        sha256_hash="abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
        phash="1122334455667788",
        timestamp_utc="2026-11-22T15:00:00Z"
    )

    signature = sign_manifest(manifest, keys['signing_private_pem'])

    # Tamper with 1 character in SHA-256 hash inside manifest
    tampered_manifest = manifest.replace("abcd1234", "bbcd1234")
    assert verify_manifest_signature(tampered_manifest, signature, keys['signing_public_pem']) is False

    # Tamper with timestamp
    tampered_manifest2 = manifest.replace("15:00:00Z", "15:00:01Z")
    assert verify_manifest_signature(tampered_manifest2, signature, keys['signing_public_pem']) is False

def test_tamper_detection_in_signature():
    """Verify that corrupting the signature bytes invalidates the verification."""
    keys = generate_user_key_pairs(key_size=2048)
    manifest = build_canonical_manifest(
        media_id="test-media-123",
        owner_id=1,
        filename="sample.png",
        file_size=1024,
        mime_type="image/png",
        sha256_hash="abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
        phash="1122334455667788",
        timestamp_utc="2026-11-22T15:00:00Z"
    )

    signature = bytearray(sign_manifest(manifest, keys['signing_private_pem']))
    signature[5] ^= 0xFF  # Corrupt single byte

    assert verify_manifest_signature(manifest, bytes(signature), keys['signing_public_pem']) is False

def test_wrong_public_key_fails_verification():
    """Verify that attempting verification with a different user's public key fails."""
    user1_keys = generate_user_key_pairs(key_size=2048)
    user2_keys = generate_user_key_pairs(key_size=2048)

    manifest = build_canonical_manifest(
        media_id="test-media-123",
        owner_id=1,
        filename="sample.png",
        file_size=1024,
        mime_type="image/png",
        sha256_hash="abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
        phash="1122334455667788",
        timestamp_utc="2026-11-22T15:00:00Z"
    )

    signature = sign_manifest(manifest, user1_keys['signing_private_pem'])

    assert verify_manifest_signature(manifest, signature, user2_keys['signing_public_pem']) is False
