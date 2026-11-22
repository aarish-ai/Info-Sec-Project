import pytest
import sqlite3
from app.core.audit_chain import compute_log_hash, append_audit_log, verify_audit_chain

def _create_test_user(db, username="audit_user"):
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO users (
            username, email, password_hash, totp_secret, role,
            public_signing_key, public_encryption_key,
            encrypted_signing_key_path, encrypted_encryption_key_path,
            kdf_salt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username, f"{username}@test.com", "fake_hash", "JBSWY3DPEHPK3PXP", "Auditor",
            "pub_sign", "pub_enc", "/path/sign", "/path/enc", b'salt_16_bytes_long'
        )
    )
    db.commit()
    return cursor.lastrowid

def test_compute_log_hash_deterministic():
    """Verify compute_log_hash produces a consistent 64-character SHA-256 hex string."""
    hash1 = compute_log_hash(1, "2026-11-22 12:00:00", 1, "LOGIN", "Success", "127.0.0.1", "0" * 64)
    hash2 = compute_log_hash(1, "2026-11-22 12:00:00", 1, "LOGIN", "Success", "127.0.0.1", "0" * 64)
    assert len(hash1) == 64
    assert hash1 == hash2

    # Any alteration changes hash
    hash3 = compute_log_hash(1, "2026-11-22 12:00:00", 1, "LOGIN", "Failure", "127.0.0.1", "0" * 64)
    assert hash1 != hash3

def test_append_audit_log_empty_table_genesis(db):
    """Appending first log entry uses genesis prev_hash ('0'*64) and computes valid current_hash."""
    log_id = append_audit_log(db, user_id=None, action="SYSTEM_INIT", details="Genesis block test", ip_address="127.0.0.1")
    assert log_id == 1

    cursor = db.cursor()
    cursor.execute("SELECT * FROM audit_log WHERE log_id = 1")
    row = cursor.fetchone()
    assert row is not None
    assert row['prev_hash'] == "0" * 64
    assert len(row['current_hash']) == 64

    # Verification passes
    is_valid, corrupted_id, msg = verify_audit_chain(db)
    assert is_valid is True
    assert corrupted_id == 0
    assert "All 1 audit log entries cryptographically intact" in msg

def test_append_audit_log_sequential_linkage(db):
    """Appending multiple log entries correctly chains each entry's prev_hash to previous current_hash."""
    user_id = _create_test_user(db, "seq_user")
    id1 = append_audit_log(db, user_id=user_id, action="REGISTER", details="User registered", ip_address="10.0.0.1")
    id2 = append_audit_log(db, user_id=user_id, action="LOGIN", details="Successful login", ip_address="10.0.0.1")
    id3 = append_audit_log(db, user_id=user_id, action="UPLOAD", details="Uploaded test.jpg", ip_address="10.0.0.1")

    assert id1 == 1
    assert id2 == 2
    assert id3 == 3

    cursor = db.cursor()
    cursor.execute("SELECT log_id, prev_hash, current_hash FROM audit_log ORDER BY log_id ASC")
    rows = cursor.fetchall()
    assert len(rows) == 3

    assert rows[0]['prev_hash'] == "0" * 64
    assert rows[1]['prev_hash'] == rows[0]['current_hash']
    assert rows[2]['prev_hash'] == rows[1]['current_hash']

    is_valid, corrupted_id, msg = verify_audit_chain(db)
    assert is_valid is True
    assert corrupted_id == 0
    assert "All 3 audit log entries cryptographically intact" in msg

def test_verify_audit_chain_detects_data_tampering(db):
    """Tampering with action or details in an intermediate row is immediately detected."""
    user_id = _create_test_user(db, "tamper_user")
    append_audit_log(db, user_id=user_id, action="EVENT_A", details="Normal event", ip_address="127.0.0.1")
    append_audit_log(db, user_id=user_id, action="EVENT_B", details="Normal event 2", ip_address="127.0.0.1")
    append_audit_log(db, user_id=user_id, action="EVENT_C", details="Normal event 3", ip_address="127.0.0.1")

    # Malicious attacker modifies details of row 2 directly in SQLite
    cursor = db.cursor()
    cursor.execute("UPDATE audit_log SET details = 'TAMPERED_CONTENT' WHERE log_id = 2")
    db.commit()

    is_valid, corrupted_id, msg = verify_audit_chain(db)
    assert is_valid is False
    assert corrupted_id == 2
    assert "Hash chain broken at Log ID 2" in msg

def test_verify_audit_chain_detects_prev_hash_tampering(db):
    """Tampering with prev_hash in an intermediate row is detected at that row."""
    user_id = _create_test_user(db, "prev_tamper_user")
    append_audit_log(db, user_id=user_id, action="EVENT_1", details="Log 1", ip_address="127.0.0.1")
    append_audit_log(db, user_id=user_id, action="EVENT_2", details="Log 2", ip_address="127.0.0.1")

    cursor = db.cursor()
    cursor.execute("UPDATE audit_log SET prev_hash = ? WHERE log_id = 2", ("f" * 64,))
    db.commit()

    is_valid, corrupted_id, msg = verify_audit_chain(db)
    assert is_valid is False
    assert corrupted_id == 2
    assert "Hash chain broken at Log ID 2" in msg

def test_verify_audit_chain_detects_row_deletion(db):
    """Deleting an intermediate row breaks the linkage for subsequent rows."""
    user_id = _create_test_user(db, "del_user")
    append_audit_log(db, user_id=user_id, action="LOG_1", details="First", ip_address="127.0.0.1")
    append_audit_log(db, user_id=user_id, action="LOG_2", details="Second to be deleted", ip_address="127.0.0.1")
    append_audit_log(db, user_id=user_id, action="LOG_3", details="Third", ip_address="127.0.0.1")

    # Attacker deletes row 2 to hide an action
    cursor = db.cursor()
    cursor.execute("DELETE FROM audit_log WHERE log_id = 2")
    db.commit()

    # Now row 3 has prev_hash pointing to deleted row 2's current_hash, but row 1's current_hash is previous
    is_valid, corrupted_id, msg = verify_audit_chain(db)
    assert is_valid is False
    assert corrupted_id == 3
    assert "Hash chain broken at Log ID 3" in msg

def test_verify_audit_chain_empty_table(db):
    """An empty audit log table is valid with 0 entries."""
    is_valid, corrupted_id, msg = verify_audit_chain(db)
    assert is_valid is True
    assert corrupted_id == 0
    assert "All 0 audit log entries cryptographically intact" in msg
