import io
import json
import pytest
from PIL import Image
from cryptography.exceptions import InvalidTag
from app.core.hashing import compute_streamed_sha256, compute_phash, compute_phash_distance
from app.core.key_management import generate_user_key_pairs
from app.core.signatures import build_canonical_manifest, sign_manifest, verify_manifest_signature
from app.core.ciphers import encrypt_media_envelope, decrypt_media_envelope
from experiments.attack_simulations import (
    simulate_pixel_tampering,
    simulate_file_replacement,
    simulate_signature_tampering,
    simulate_wrong_key_verification,
    simulate_unauthorized_decryption,
    simulate_ciphertext_bitflip,
    run_named_attack_simulation,
    ATTACK_CATALOG
)

def _generate_test_image_bytes():
    from PIL import ImageDraw
    img = Image.new('RGB', (100, 100), color=(100, 150, 200))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 80, 80], fill=(20, 50, 90), outline=(255, 0, 0))
    draw.ellipse([25, 25, 75, 75], fill=(240, 200, 50))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def test_simulate_pixel_tampering():
    """Verify pixel tampering changes SHA-256 while preserving close visual pHash."""
    original_bytes = _generate_test_image_bytes()
    tampered_bytes = simulate_pixel_tampering(original_bytes)

    assert tampered_bytes != original_bytes

    orig_sha = compute_streamed_sha256(io.BytesIO(original_bytes))
    tamp_sha = compute_streamed_sha256(io.BytesIO(tampered_bytes))
    assert orig_sha != tamp_sha, "Pixel tampering must change the SHA-256 fingerprint"

    orig_phash = compute_phash(io.BytesIO(original_bytes))
    tamp_phash = compute_phash(io.BytesIO(tampered_bytes))
    distance = compute_phash_distance(orig_phash, tamp_phash)
    assert 0 <= distance <= 10, "Subtle pixel tampering should keep perceptual distance low (visual similarity preserved)"

def test_simulate_file_replacement():
    """Verify file replacement produces a completely different SHA-256 and high pHash distance."""
    original_bytes = _generate_test_image_bytes()
    replaced_bytes = simulate_file_replacement(original_bytes)

    assert replaced_bytes != original_bytes
    orig_sha = compute_streamed_sha256(io.BytesIO(original_bytes))
    rep_sha = compute_streamed_sha256(io.BytesIO(replaced_bytes))
    assert orig_sha != rep_sha

    orig_phash = compute_phash(io.BytesIO(original_bytes))
    rep_phash = compute_phash(io.BytesIO(replaced_bytes))
    distance = compute_phash_distance(orig_phash, rep_phash)
    assert distance > 10, "File replacement should produce high perceptual distance"

def test_simulate_signature_tampering():
    """Verify tampering manifest metadata or signature causes RSA-PSS verification to fail."""
    keys = generate_user_key_pairs(key_size=2048)
    manifest = build_canonical_manifest(
        media_id="test-sim-001",
        owner_id=1,
        filename="test.png",
        file_size=5000,
        mime_type="image/png",
        sha256_hash="1111222233334444111122223333444411112222333344441111222233334444",
        phash="1234567890abcdef",
        timestamp_utc="2026-11-22T12:00:00Z"
    )
    sig = sign_manifest(manifest, keys['signing_private_pem'])
    assert verify_manifest_signature(manifest, sig, keys['signing_public_pem']) is True

    tampered_manifest, tampered_sig = simulate_signature_tampering(manifest, sig)
    assert (tampered_manifest != manifest) or (tampered_sig != sig)

    # Verification must fail
    is_valid = verify_manifest_signature(tampered_manifest, tampered_sig, keys['signing_public_pem'])
    assert is_valid is False

def test_simulate_wrong_key_verification():
    """Verify attempting to verify a signature with a different public key returns False."""
    key_alice = generate_user_key_pairs(key_size=2048)
    key_bob = generate_user_key_pairs(key_size=2048)

    manifest = build_canonical_manifest(
        media_id="test-sim-002",
        owner_id=1,
        filename="doc.png",
        file_size=1024,
        mime_type="image/png",
        sha256_hash="aaaabbbbccccddddaaaabbbbccccddddaaaabbbbccccddddaaaabbbbccccdddd",
        phash="abcdef0123456789",
        timestamp_utc="2026-11-22T12:00:00Z"
    )
    sig = sign_manifest(manifest, key_alice['signing_private_pem'])

    result = simulate_wrong_key_verification(manifest, sig, key_bob['signing_public_pem'])
    assert result is False

def test_simulate_unauthorized_decryption():
    """Verify unwrapping AES key with wrong private key fails and returns False."""
    key_alice = generate_user_key_pairs(key_size=2048)
    key_bob = generate_user_key_pairs(key_size=2048)

    plaintext = b"Confidential Medical Imagery"
    envelope = encrypt_media_envelope(plaintext, key_alice['encryption_public_pem'])

    result = simulate_unauthorized_decryption(
        envelope['wrapped_aes_key'],
        key_bob['encryption_private_pem']
    )
    assert result is False

def test_simulate_ciphertext_bitflip():
    """Verify bit-flipping ciphertext causes AES-GCM decryption to raise InvalidTag."""
    keys = generate_user_key_pairs(key_size=2048)
    plaintext = b"Highly Sensitive Classified Intelligence"
    envelope = encrypt_media_envelope(plaintext, keys['encryption_public_pem'])

    tampered_ct = simulate_ciphertext_bitflip(envelope['ciphertext'])
    assert tampered_ct != envelope['ciphertext']

    with pytest.raises(InvalidTag):
        decrypt_media_envelope(
            ciphertext=tampered_ct,
            wrapped_aes_key=envelope['wrapped_aes_key'],
            nonce=envelope['nonce'],
            auth_tag=envelope['auth_tag'],
            owner_private_enc_key_pem=keys['encryption_private_pem']
        )

def test_run_named_attack_simulation_all_catalog():
    """Verify all 6 attacks in the catalog run cleanly and report BLOCKED / DETECTED."""
    assert len(ATTACK_CATALOG) == 6
    for attack_id in ATTACK_CATALOG:
        res = run_named_attack_simulation(attack_id)
        assert res['success'] is True
        assert res['attack_name'] == attack_id
        assert res['status'] in ('BLOCKED', 'DETECTED')
        assert 'diagnostic_log' in res
        assert 'cryptographic_defense' in res

def test_experiments_routes(client):
    """Verify /experiments renders dashboard and /experiments/run/<name> executes attacks."""
    # Unauthenticated access redirects or 401
    res_unauth = client.get('/experiments', headers={'Accept': 'application/json'})
    assert res_unauth.status_code == 401

    # Login test user
    client.post('/auth/register', json={
        'username': 'exp_user',
        'email': 'exp@example.com',
        'password': 'ExpPassword#2026',
        'role': 'User'
    })
    # login requires TOTP or let's setup 2fa
    # Note: /auth/register returns totp_secret
    # In test, we can log in with totp
    import pyotp
    reg_data = client.post('/auth/register', json={
        'username': 'exp_user_2',
        'email': 'exp2@example.com',
        'password': 'ExpPassword#2026',
        'role': 'User'
    }).get_json()
    totp = pyotp.TOTP(reg_data['totp_secret'])
    client.post('/auth/setup-2fa', json={'code': totp.now()})

    # GET /experiments
    res = client.get('/experiments')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Security Attack Simulation Suite' in html
    assert 'pixel_tampering' in html
    assert 'file_replacement' in html

    # POST /experiments/run/pixel_tampering
    res_run = client.post('/experiments/run/pixel_tampering', headers={'Accept': 'application/json'})
    assert res_run.status_code == 200
    data = res_run.get_json()
    assert data['success'] is True
    assert data['status'] == 'DETECTED'

    # POST invalid attack name
    res_invalid = client.post('/experiments/run/nonexistent_attack', headers={'Accept': 'application/json'})
    assert res_invalid.status_code == 404
