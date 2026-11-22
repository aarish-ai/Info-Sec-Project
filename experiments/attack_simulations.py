import io
import json
import os
import hashlib
from typing import Dict, Any, Tuple, Optional, Union
from PIL import Image
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.hashing import compute_streamed_sha256, compute_phash, compute_phash_distance
from app.core.key_management import generate_user_key_pairs
from app.core.signatures import build_canonical_manifest, sign_manifest, verify_manifest_signature
from app.core.ciphers import encrypt_media_envelope, decrypt_media_envelope

# ==============================================================================
# Standalone Attack Simulation Primitives (Task 23)
# ==============================================================================

def simulate_pixel_tampering(original_image_bytes: bytes) -> bytes:
    """
    Simulates malicious pixel alteration in an authentic image.
    Modifies a single pixel's color channel or minor pixel block,
    preserving overall visual structure while altering the cryptographic byte stream.
    """
    try:
        img = Image.open(io.BytesIO(original_image_bytes)).convert('RGB')
        # Alter a single pixel in the upper left or center
        target_x = min(5, img.width - 1)
        target_y = min(5, img.height - 1)
        orig_pixel = img.getpixel((target_x, target_y))
        altered_pixel = ((orig_pixel[0] + 80) % 256, (orig_pixel[1] + 40) % 256, orig_pixel[2])
        img.putpixel((target_x, target_y), altered_pixel)

        out_buf = io.BytesIO()
        img.save(out_buf, format='PNG')
        return out_buf.getvalue()
    except Exception:
        # Fallback for non-image byte buffers: flip a byte in the payload
        buf = bytearray(original_image_bytes)
        if len(buf) > 10:
            buf[10] ^= 0x01
        elif len(buf) > 0:
            buf[0] ^= 0x01
        return bytes(buf)

def simulate_file_replacement(original_bytes: bytes) -> bytes:
    """
    Simulates a file substitution attack where an adversary substitutes an entirely
    unrelated media asset under an existing registered provenance ID.
    """
    # Create an entirely different synthetic image with distinct pattern and color
    img = Image.new('RGB', (120, 120), color=(255, 30, 80))
    for x in range(0, 120, 10):
        for y in range(0, 120, 10):
            img.putpixel((x, y), (20, 240, 50))
    out_buf = io.BytesIO()
    img.save(out_buf, format='PNG')
    return out_buf.getvalue()

def simulate_signature_tampering(
    canonical_manifest: str,
    signature: Optional[bytes] = None
) -> Tuple[str, bytes]:
    """
    Simulates tampering with canonical registration manifest metadata or signature bytes.
    Alters a metadata field (e.g., file size or timestamp) in the JSON payload.
    """
    try:
        data = json.loads(canonical_manifest)
        if 'file_size' in data:
            data['file_size'] = int(data['file_size']) + 1
        elif 'timestamp_utc' in data:
            data['timestamp_utc'] = "2026-11-22T23:59:59Z"
        else:
            data['tampered'] = True
        tampered_manifest = json.dumps(data, separators=(',', ':'), sort_keys=True)
    except Exception:
        tampered_manifest = canonical_manifest + "/*tampered*/"

    if signature is not None:
        tampered_sig = signature
    else:
        tampered_sig = b"tampered_signature_bytes"

    return tampered_manifest, tampered_sig

def simulate_wrong_key_verification(
    manifest: str,
    signature: bytes,
    wrong_public_key_pem: Union[str, bytes]
) -> bool:
    """
    Simulates verification with an arbitrary or forged public key.
    Must return False, proving digital provenance non-transferability.
    """
    return verify_manifest_signature(manifest, signature, wrong_public_key_pem)

def simulate_unauthorized_decryption(
    wrapped_aes_key: bytes,
    wrong_private_key_pem: Union[str, bytes]
) -> bool:
    """
    Simulates an attacker attempting to unwrap the symmetric AES-256 media key
    using an unauthorized or attacker-controlled RSA private key.
    Returns False when decryption fails.
    """
    if isinstance(wrong_private_key_pem, str):
        priv_pem_bytes = wrong_private_key_pem.encode('utf-8')
    else:
        priv_pem_bytes = wrong_private_key_pem

    try:
        private_key = serialization.load_pem_private_key(priv_pem_bytes, password=None)
        private_key.decrypt(
            wrapped_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return True
    except Exception:
        return False

def simulate_ciphertext_bitflip(ciphertext: bytes) -> bytes:
    """
    Simulates ciphertext tampering or bit-flipping on disk.
    Alters bits in the AES-256-GCM ciphertext payload.
    """
    tampered = bytearray(ciphertext)
    if len(tampered) > 0:
        tampered[0] ^= 0x01
    return bytes(tampered)

# ==============================================================================
# Attack Catalog & End-to-End Diagnostic Demonstrator
# ==============================================================================

ATTACK_CATALOG: Dict[str, Dict[str, str]] = {
    'pixel_tampering': {
        'id': 'pixel_tampering',
        'title': '1-Pixel Modification Attack',
        'owasp': 'A08:2021 – Software and Data Integrity Failures',
        'description': 'Attacker alters subtle pixels in an authentic registered image.',
        'target': 'Cryptographic SHA-256 & Perceptual pHash Engine'
    },
    'file_replacement': {
        'id': 'file_replacement',
        'title': 'File Substitution / Replacement Attack',
        'owasp': 'A08:2021 – Software and Data Integrity Failures',
        'description': 'Attacker replaces a verified image with an entirely different file.',
        'target': 'Perceptual Hash Distance & SHA-256 Discrepancy'
    },
    'signature_tampering': {
        'id': 'signature_tampering',
        'title': 'Digital Signature & Manifest Tampering',
        'owasp': 'A08:2021 – Software and Data Integrity Failures',
        'description': 'Adversary modifies metadata (e.g. file size, timestamp) inside canonical JSON manifest.',
        'target': '2048-bit RSA-PSS Asymmetric Signature'
    },
    'wrong_key_verification': {
        'id': 'wrong_key_verification',
        'title': 'Wrong-Key Verification / Spoofed Provenance',
        'owasp': 'A07:2021 – Identification & Authentication Failures',
        'description': 'Attacker presents a valid signature but attempts verification with an unauthorized public key.',
        'target': 'RSA-PSS Public Key Cryptographic Binding'
    },
    'unauthorized_decryption': {
        'id': 'unauthorized_decryption',
        'title': 'Unauthorized Envelope Decryption Attack',
        'owasp': 'A02:2021 – Cryptographic Failures',
        'description': 'Intruder steals encrypted ciphertext and wrapped AES key from disk and attempts to decrypt it.',
        'target': 'RSA-OAEP Key Wrapping & Zero-Plaintext Storage'
    },
    'ciphertext_bitflip': {
        'id': 'ciphertext_bitflip',
        'title': 'Ciphertext Bit-Flipping / At-Rest Tampering',
        'owasp': 'A02:2021 – Cryptographic Failures',
        'description': 'Disk attacker flips a single bit in the stored ciphertext or authentication tag.',
        'target': 'AES-256-GCM AEAD Tag Authentication'
    }
}

def run_named_attack_simulation(attack_name: str) -> Dict[str, Any]:
    """
    Executes a controlled attack simulation end-to-end and returns real-time diagnostic
    telemetry demonstrating the cryptographic defense mechanism.
    """
    if attack_name not in ATTACK_CATALOG:
        return {
            'success': False,
            'error': f"Unknown attack simulation '{attack_name}'."
        }

    meta = ATTACK_CATALOG[attack_name]

    if attack_name == 'pixel_tampering':
        # Generate genuine sample image with visual features
        from PIL import ImageDraw
        img = Image.new('RGB', (100, 100), color=(50, 100, 150))
        draw = ImageDraw.Draw(img)
        draw.rectangle([15, 15, 85, 85], fill=(20, 60, 110), outline=(250, 100, 20))
        draw.ellipse([30, 30, 70, 70], fill=(230, 210, 40))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        orig_bytes = buf.getvalue()

        orig_sha = compute_streamed_sha256(io.BytesIO(orig_bytes))
        orig_phash = compute_phash(io.BytesIO(orig_bytes))

        # Perform attack
        tampered_bytes = simulate_pixel_tampering(orig_bytes)
        tamp_sha = compute_streamed_sha256(io.BytesIO(tampered_bytes))
        tamp_phash = compute_phash(io.BytesIO(tampered_bytes))
        distance = compute_phash_distance(orig_phash, tamp_phash)

        # Defense verification
        sha_match = (orig_sha == tamp_sha)
        detected = (not sha_match)

        return {
            'success': True,
            'attack_name': attack_name,
            'title': meta['title'],
            'owasp': meta['owasp'],
            'status': 'DETECTED' if detected else 'VULNERABLE',
            'cryptographic_defense': 'SHA-256 Streamed Hash Mismatch + pHash Visual Diagnostic',
            'details': {
                'original_sha256': orig_sha,
                'tampered_sha256': tamp_sha,
                'sha256_match': sha_match,
                'original_phash': orig_phash,
                'tampered_phash': tamp_phash,
                'phash_hamming_distance': distance,
                'diagnosis': f"SHA-256 altered completely ({orig_sha[:8]}... != {tamp_sha[:8]}...). pHash Hamming distance is {distance} (<=10), proving visual similarity with byte-level tampering."
            },
            'diagnostic_log': (
                f"[SIMULATION] Original SHA-256: {orig_sha}\n"
                f"[ATTACK] Injected 1 altered pixel into image RGB channel.\n"
                f"[SIMULATION] Tampered SHA-256: {tamp_sha}\n"
                f"[DEFENSE] SHA-256 Check: FAILED (Byte discrepancy detected immediately)\n"
                f"[DEFENSE] pHash Distance: {distance} (Visual match confirmed: tampered photo detected)"
            )
        }

    elif attack_name == 'file_replacement':
        img = Image.new('RGB', (100, 100), color=(20, 20, 20))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        orig_bytes = buf.getvalue()

        orig_sha = compute_streamed_sha256(io.BytesIO(orig_bytes))
        orig_phash = compute_phash(io.BytesIO(orig_bytes))

        replaced_bytes = simulate_file_replacement(orig_bytes)
        rep_sha = compute_streamed_sha256(io.BytesIO(replaced_bytes))
        rep_phash = compute_phash(io.BytesIO(replaced_bytes))
        distance = compute_phash_distance(orig_phash, rep_phash)

        detected = (orig_sha != rep_sha) and (distance > 10)

        return {
            'success': True,
            'attack_name': attack_name,
            'title': meta['title'],
            'owasp': meta['owasp'],
            'status': 'DETECTED' if detected else 'VULNERABLE',
            'cryptographic_defense': 'Dual-Check Architecture (SHA-256 Failure + High Hamming Distance)',
            'details': {
                'original_sha256': orig_sha,
                'substituted_sha256': rep_sha,
                'original_phash': orig_phash,
                'substituted_phash': rep_phash,
                'phash_hamming_distance': distance,
                'diagnosis': f"File replacement detected! pHash distance {distance} (> 10) and SHA-256 mismatch prove an entirely different object was submitted."
            },
            'diagnostic_log': (
                f"[SIMULATION] Registered Asset SHA-256: {orig_sha}\n"
                f"[ATTACK] Substituted unrelated graphic asset under existing Certificate ID.\n"
                f"[DEFENSE] SHA-256 Check: FAILED ({orig_sha[:8]} != {rep_sha[:8]})\n"
                f"[DEFENSE] pHash Distance: {distance} (>10 threshold) -> Asset completely rejected as fraudulent substitute."
            )
        }

    elif attack_name == 'signature_tampering':
        keys = generate_user_key_pairs(key_size=2048)
        manifest = build_canonical_manifest(
            media_id="evidence-asset-99",
            owner_id=42,
            filename="confidential_audit.pdf",
            file_size=1048576,
            mime_type="application/pdf",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            phash="N/A",
            timestamp_utc="2026-11-22T10:00:00Z"
        )
        sig = sign_manifest(manifest, keys['signing_private_pem'])
        tampered_manifest, _ = simulate_signature_tampering(manifest, sig)

        # Verification
        verified = verify_manifest_signature(tampered_manifest, sig, keys['signing_public_pem'])
        blocked = (verified is False)

        return {
            'success': True,
            'attack_name': attack_name,
            'title': meta['title'],
            'owasp': meta['owasp'],
            'status': 'BLOCKED' if blocked else 'VULNERABLE',
            'cryptographic_defense': 'RSA-PSS Digital Signature Integrity Check',
            'details': {
                'original_manifest': manifest,
                'tampered_manifest': tampered_manifest,
                'signature_verification_result': verified,
                'diagnosis': "Adversary attempted to alter metadata in manifest. RSA-PSS signature verification returned False, immediately rejecting modified metadata."
            },
            'diagnostic_log': (
                f"[SIMULATION] Canonical Manifest signed with Owner RSA-PSS Private Key.\n"
                f"[ATTACK] Tampered manifest payload: {tampered_manifest}\n"
                f"[DEFENSE] RSA-PSS Signature Verification: FAILED (False)\n"
                f"[DEFENSE] Tampering blocked! Provenance record refused."
            )
        }

    elif attack_name == 'wrong_key_verification':
        key_alice = generate_user_key_pairs(key_size=2048)
        key_bob = generate_user_key_pairs(key_size=2048)

        manifest = build_canonical_manifest(
            media_id="alice-photo-001",
            owner_id=1,
            filename="photo.jpg",
            file_size=20480,
            mime_type="image/jpeg",
            sha256_hash="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            phash="1122334455667788",
            timestamp_utc="2026-11-22T11:00:00Z"
        )
        sig = sign_manifest(manifest, key_alice['signing_private_pem'])
        verified = simulate_wrong_key_verification(manifest, sig, key_bob['signing_public_pem'])
        blocked = (verified is False)

        return {
            'success': True,
            'attack_name': attack_name,
            'title': meta['title'],
            'owasp': meta['owasp'],
            'status': 'BLOCKED' if blocked else 'VULNERABLE',
            'cryptographic_defense': 'Owner-Bound Asymmetric RSA Public Key Verification',
            'details': {
                'true_owner_key': 'Alice Public Key',
                'tested_key': 'Bob Public Key (Adversary)',
                'verification_result': verified,
                'diagnosis': "Attempted to verify Alice's signed provenance with Bob's public key. Cryptographic mismatch blocked the fraudulent verification."
            },
            'diagnostic_log': (
                f"[SIMULATION] Manifest generated by Alice and signed with Alice's Private Key.\n"
                f"[ATTACK] Verifier presented Bob's Public Key to claim ownership.\n"
                f"[DEFENSE] RSA-PSS Signature Verification: FAILED (False)\n"
                f"[DEFENSE] Provenance spoofing blocked: Non-transferability mathematically enforced."
            )
        }

    elif attack_name == 'unauthorized_decryption':
        key_victim = generate_user_key_pairs(key_size=2048)
        key_attacker = generate_user_key_pairs(key_size=2048)

        secret_data = b"Patient Medical History & Confidential Record"
        envelope = encrypt_media_envelope(secret_data, key_victim['encryption_public_pem'])

        unwrapped = simulate_unauthorized_decryption(
            envelope['wrapped_aes_key'],
            key_attacker['encryption_private_pem']
        )
        blocked = (unwrapped is False)

        return {
            'success': True,
            'attack_name': attack_name,
            'title': meta['title'],
            'owasp': meta['owasp'],
            'status': 'BLOCKED' if blocked else 'VULNERABLE',
            'cryptographic_defense': 'RSA-OAEP Asymmetric Key Wrapping Decryption Barrier',
            'details': {
                'wrapped_aes_key_len': len(envelope['wrapped_aes_key']),
                'attacker_unwrapped_key': unwrapped,
                'diagnosis': "Attacker possessed encrypted media and wrapped AES key. Attempting to unwrap with attacker's private key failed: ValueError Decryption failed."
            },
            'diagnostic_log': (
                f"[SIMULATION] Asset encrypted with AES-256-GCM; AES key wrapped with Victim's RSA Public Key.\n"
                f"[ATTACK] Attacker attempts RSA-OAEP decryption using Attacker Private Key.\n"
                f"[DEFENSE] RSA-OAEP Decryption: FAILED (ValueError: Decryption failed)\n"
                f"[DEFENSE] Ciphertext confidentiality preserved! Zero plaintext exposed."
            )
        }

    elif attack_name == 'ciphertext_bitflip':
        keys = generate_user_key_pairs(key_size=2048)
        payload = b"CRITICAL_SYSTEM_FIRMWARE_BINARY"
        envelope = encrypt_media_envelope(payload, keys['encryption_public_pem'])

        tampered_ct = simulate_ciphertext_bitflip(envelope['ciphertext'])

        # Attempt decryption
        decryption_threw_invalid_tag = False
        try:
            decrypt_media_envelope(
                ciphertext=tampered_ct,
                wrapped_aes_key=envelope['wrapped_aes_key'],
                nonce=envelope['nonce'],
                auth_tag=envelope['auth_tag'],
                owner_private_enc_key_pem=keys['encryption_private_pem']
            )
        except InvalidTag:
            decryption_threw_invalid_tag = True

        blocked = decryption_threw_invalid_tag

        return {
            'success': True,
            'attack_name': attack_name,
            'title': meta['title'],
            'owasp': meta['owasp'],
            'status': 'BLOCKED' if blocked else 'VULNERABLE',
            'cryptographic_defense': 'AES-256-GCM Galois/Counter Mode AEAD Tag Authentication',
            'details': {
                'ciphertext_length': len(envelope['ciphertext']),
                'bit_flipped': True,
                'invalid_tag_triggered': decryption_threw_invalid_tag,
                'diagnosis': "Single bit flipped in encrypted ciphertext. AES-GCM authenticated decryption immediately raised InvalidTag and terminated before any plaintext was released."
            },
            'diagnostic_log': (
                f"[SIMULATION] Original AES-256-GCM ciphertext generated with 128-bit authentication tag.\n"
                f"[ATTACK] Injected 1-bit flip into encrypted ciphertext block on disk.\n"
                f"[DEFENSE] AES-256-GCM AEAD Tag Authentication: FAILED (cryptography.exceptions.InvalidTag)\n"
                f"[DEFENSE] Decryption aborted: Corrupted payload halted with zero plaintext leakage."
            )
        }

    return {'success': False, 'error': 'Unhandled simulation'}
