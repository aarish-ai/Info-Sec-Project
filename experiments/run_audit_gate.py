import os
import sys
import io
import re
import tempfile
from pathlib import Path

# Set up project root
PROJECT_ROOT = Path(r"d:\Projects\Unii\IS Project")
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.database.db import get_db, init_db
from app.core.ciphers import encrypt_media_envelope, decrypt_media_envelope
from app.core.key_management import generate_user_key_pairs
from app.core.signatures import sign_manifest, verify_manifest_signature, build_canonical_manifest
from app.core.hashing import compute_streamed_sha256, compute_phash, compute_phash_distance
from app.core.audit_chain import append_audit_log, verify_audit_chain
from PIL import Image
import pyotp

print("=" * 60)
print("TASK 25 PENETRATION & FINAL SYSTEM AUDIT GATE VERIFICATION")
print("=" * 60)

# Check 1: IDOR Verification
print("\n[CHECK 1] IDOR Verification (/media/<media_id>/download)")
db_fd, db_path = tempfile.mkstemp(suffix='.db')
key_dir = tempfile.mkdtemp(prefix='gate_keys_')
media_dir = tempfile.mkdtemp(prefix='gate_media_')

app = create_app({
    'TESTING': True,
    'DATABASE_PATH': db_path,
    'KEY_STORAGE_DIR': key_dir,
    'ENCRYPTED_MEDIA_DIR': media_dir,
    'SECRET_KEY': 'audit-test-key-gate',
    'SECURE_MODE': True
})
with app.app_context():
    init_db()

client = app.test_client()

def register_and_login(username, role='User'):
    res = client.post('/auth/register', json={
        'username': username,
        'email': f'{username}@example.com',
        'password': 'GatePassword#2026!',
        'role': role
    })
    data = res.get_json()
    totp = pyotp.TOTP(data['totp_secret'])
    client.post('/auth/setup-2fa', json={'code': totp.now()})
    return data['user_id']

user_a_id = register_and_login('alice')
png_content = b'\x89PNG\r\n\x1a\n' + b'Alice_Confidential_File_Content_9999'
up = client.post(
    '/media/upload',
    data={'file': (io.BytesIO(png_content), 'alice_confidential.png')},
    content_type='multipart/form-data',
    headers={'Accept': 'application/json'}
)
assert up.status_code == 201, f"Alice upload failed: {up.data}"
media_id = up.get_json()['media_id']

# Log out Alice and log in Bob (attacker)
client.post('/auth/logout')
register_and_login('bob_attacker')

# SECURE_MODE = True
app.config['SECURE_MODE'] = True
r_sec = client.get(f'/media/{media_id}/download', headers={'Accept': 'application/json'})
print(f"  -> SECURE_MODE=True: Status={r_sec.status_code}, Response={r_sec.get_json()}")
assert r_sec.status_code == 403, f"Expected 403 in SECURE_MODE=True, got {r_sec.status_code}"

# SECURE_MODE = False
app.config['SECURE_MODE'] = False
r_vuln = client.get(f'/media/{media_id}/download')
print(f"  -> SECURE_MODE=False: Status={r_vuln.status_code}, Content-Disposition={r_vuln.headers.get('Content-Disposition')}")
assert r_vuln.status_code == 200, f"Expected 200 in SECURE_MODE=False, got {r_vuln.status_code}"
assert 'attachment' in r_vuln.headers.get('Content-Disposition', '')
print("  [+] CHECK 1 (IDOR dual-mode): VERIFIED SUCCESS")


# Check 2: SQLi Verification
print("\n[CHECK 2] SQLi Verification (/admin/search)")
client.post('/auth/logout')
register_and_login('admin_gate', role='Admin')

sqli_payload = "' OR '1'='1"

# SECURE_MODE = True (Parameterized, literal search)
app.config['SECURE_MODE'] = True
r_sqli_sec = client.get(f'/admin/search?q={sqli_payload}', headers={'Accept': 'application/json'})
sec_json = r_sqli_sec.get_json()
print(f"  -> SECURE_MODE=True: Status={r_sqli_sec.status_code}, Matched Accounts={sec_json['count']}")
assert sec_json['count'] == 0, f"Expected 0 for literal SQL string, got {sec_json['count']}"

# SECURE_MODE = False (String concatenation, SQL injected)
app.config['SECURE_MODE'] = False
r_sqli_vuln = client.get(f'/admin/search?q={sqli_payload}', headers={'Accept': 'application/json'})
vuln_json = r_sqli_vuln.get_json()
print(f"  -> SECURE_MODE=False: Status={r_sqli_vuln.status_code}, Injected Result Count={vuln_json['count']}")
assert vuln_json['count'] > 0, f"Expected > 0 for SQL injection, got {vuln_json['count']}"
print("  [+] CHECK 2 (SQLi dual-mode): VERIFIED SUCCESS")


# Check 3: Audit Trail Chain Tamper Detection
print("\n[CHECK 3] Audit Trail Chain Tamper Detection (verify_audit_chain)")
with app.app_context():
    db = get_db()
    c = db.cursor()

    # Append multiple audit logs to form a rich hash chain
    append_audit_log(db, user_id=1, action="FILE_UPLOAD", details="File A uploaded", ip_address="127.0.0.1")
    append_audit_log(db, user_id=1, action="FILE_DOWNLOAD", details="File A downloaded", ip_address="127.0.0.1")
    append_audit_log(db, user_id=2, action="LOGIN_SUCCESS", details="User Bob logged in", ip_address="192.168.1.50")
    db.commit()

    # Verify intact chain
    is_valid, broken_id, msg = verify_audit_chain(db)
    print(f"  -> Intact chain verification: is_valid={is_valid}, broken_id={broken_id}, msg='{msg}'")
    assert is_valid is True

    # Tamper with row at log_id = 3
    c.execute("SELECT log_id, action, details FROM audit_log ORDER BY log_id ASC LIMIT 1 OFFSET 2")
    target_row = c.fetchone()
    tamper_id = target_row['log_id']
    print(f"  -> Modifying row log_id={tamper_id} (action={target_row['action']}) in sqlite audit_log table...")
    c.execute("UPDATE audit_log SET details = ? WHERE log_id = ?", ("MALICIOUS_LOG_TAMPER_TEST", tamper_id))
    db.commit()

    is_valid_t, broken_id_t, msg_t = verify_audit_chain(db)
    print(f"  -> Post-tamper verification: is_valid={is_valid_t}, broken_id={broken_id_t}, msg='{msg_t}'")
    assert is_valid_t is False
    assert broken_id_t == tamper_id, f"Expected pinpointed row {tamper_id}, got {broken_id_t}"
print("  [+] CHECK 3 (Audit chain cryptographic linkage): VERIFIED SUCCESS")


# Check 4: Zero-Plaintext Policy
print("\n[CHECK 4] Zero-Plaintext Storage Policy")
with app.app_context():
    storage_dir = Path(app.config.get('STORAGE_DIR', 'storage'))
    temp_dir = storage_dir / 'temp'
    if temp_dir.exists():
        temp_files = list(temp_dir.glob('*'))
        print(f"  -> Files in temporary upload cache: {len(temp_files)}")
        assert len(temp_files) == 0, f"Found unencrypted temporary upload files: {temp_files}"
    else:
        print("  -> Temporary unencrypted cache folder cleanly unmounted/empty.")
    
    # Check encrypted directory contains only encrypted blobs
    enc_dir = storage_dir / 'encrypted'
    if enc_dir.exists():
        enc_files = list(enc_dir.glob('*'))
        print(f"  -> Confirmed {len(enc_files)} encrypted files stored in encrypted storage.")
        for ef in enc_files:
            content = ef.read_bytes()
            assert not content.startswith(b'\x89PNG'), f"Encrypted file {ef.name} has plaintext PNG header!"
            assert not content.startswith(b'\xff\xd8\xff'), f"Encrypted file {ef.name} has plaintext JPEG header!"
print("  [+] CHECK 4 (Zero-plaintext policy): VERIFIED SUCCESS")


# Check 5: Cryptographic Integrity
print("\n[CHECK 5] Cryptographic Integrity Verification")
# AES-256-GCM Envelope Encryption
keys = generate_user_key_pairs()
enc_priv, enc_pub = keys['encryption_private_pem'], keys['encryption_public_pem']
sign_priv, sign_pub = keys['signing_private_pem'], keys['signing_public_pem']

test_data = b"MediaGuard_Confidential_Cryptographic_Test_Payload" * 10
env = encrypt_media_envelope(test_data, enc_pub)
ciphertext, wrapped_key, nonce, tag = env['ciphertext'], env['wrapped_aes_key'], env['nonce'], env['auth_tag']
decrypted = decrypt_media_envelope(ciphertext, wrapped_key, nonce, tag, enc_priv)
assert decrypted == test_data, "Decrypted plaintext does not match input!"
print("  -> AES-256-GCM Envelope Encryption & RSA Decryption: Roundtrip Confirmed")

# RSA-PSS Manifest Sign & Verify
manifest = build_canonical_manifest("m-1", 1, "test.png", 1024, "image/png", "a"*64, "b"*16, "2026-11-22T12:00:00Z")
sig = sign_manifest(manifest, sign_priv)
assert verify_manifest_signature(manifest, sig, sign_pub) is True
print("  -> RSA-PSS 4096-bit Digital Signature: Genuine Signature Verified")

# Tamper Manifest
tampered_manifest = manifest.replace("test.png", "malicious.exe")
assert verify_manifest_signature(tampered_manifest, sig, sign_pub) is False
print("  -> RSA-PSS Tamper Detection: Tampered Manifest Rejected")

# Wrong Key
other_keys = generate_user_key_pairs()
other_pub = other_keys['signing_public_pem']
assert verify_manifest_signature(manifest, sig, other_pub) is False
print("  -> RSA-PSS Wrong Key Detection: Impostor Public Key Rejected")

# pHash Diagnostic Hamming Distance
img_a = Image.new("RGB", (100, 100), color="white")
img_b = Image.new("RGB", (100, 100), color="black")
b_a = io.BytesIO()
img_a.save(b_a, format="PNG")
b_a.seek(0)
b_b = io.BytesIO()
img_b.save(b_b, format="PNG")
b_b.seek(0)
ph_a = compute_phash(b_a)
ph_b = compute_phash(b_b)
dist = compute_phash_distance(ph_a, ph_b)
print(f"  -> Perceptual Hash (pHash) Hamming Distance: {dist} (pHash_A={ph_a}, pHash_B={ph_b})")
assert dist > 0
print("  [+] CHECK 5 (Cryptographic primitives): VERIFIED SUCCESS")


# Check 6: Frontend Anti-Vibecoding (Zero inline styles)
print("\n[CHECK 6] Frontend Anti-Vibecoding (Zero Inline Styles across all templates)")
templates_dir = PROJECT_ROOT / "app" / "templates"
template_files = sorted(list(templates_dir.rglob("*.html")))
style_attr_pattern = re.compile(r'style\s*=\s*[\"\'][^\"\']*[\"\']', re.IGNORECASE)

violations = {}
for tf in template_files:
    code = tf.read_text(encoding='utf-8')
    matches = style_attr_pattern.findall(code)
    if matches:
        violations[tf.name] = matches

print(f"  -> Total templates scanned: {len(template_files)}")
for tf in template_files:
    print(f"     * {tf.relative_to(PROJECT_ROOT)}")

if violations:
    print(f"  [-] Violations found: {violations}")
    sys.exit(1)
else:
    print("  -> Exact count of inline style occurrences: 0")
print("  [+] CHECK 6 (Frontend zero inline styles): VERIFIED SUCCESS")

print("\n" + "=" * 60)
print("AUDIT GATE RESULT: ALL 6 SECURITY GATES FULLY VERIFIED")
print("=" * 60)

# Clean up temp files
import shutil
os.close(db_fd)
if os.path.exists(db_path):
    try:
        os.remove(db_path)
    except OSError:
        pass
shutil.rmtree(key_dir, ignore_errors=True)
shutil.rmtree(media_dir, ignore_errors=True)
