import pytest
from app.core.auth_manager import (
    hash_password,
    verify_password,
    check_account_lockout,
    record_failed_attempt,
    reset_failed_attempts,
)
from app.core.key_management import generate_salt

def test_hash_password_and_verification():
    """Verify that hash_password produces valid Argon2id hash and verifies correctly."""
    password = "CorrectHorseBatteryStaple!2026"
    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2id$")
    assert verify_password(password_hash, password) is True
    assert verify_password(password_hash, "WrongPassword!2026") is False
    assert verify_password(password_hash, "") is False

def test_verify_password_invalid_hash_format():
    """Verify that corrupt or malformed hashes return False gracefully without unhandled crashes."""
    assert verify_password("not-a-valid-argon2-hash", "password") is False
    assert verify_password("", "password") is False

def test_account_lockout_workflow(app, db):
    """Verify account lockout escalation after 5 failed attempts and reset on success."""
    # Insert test user
    salt = generate_salt(16)
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO users (
            username, email, password_hash, totp_secret, role,
            public_signing_key, public_encryption_key,
            encrypted_signing_key_path, encrypted_encryption_key_path,
            kdf_salt, is_locked, failed_login_attempts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
        """,
        (
            "alice_lockout_test",
            "alice@example.com",
            hash_password("AliceSecret123!"),
            "JBSWY3DPEHPK3PXP",
            "User",
            "pub_sign_pem",
            "pub_enc_pem",
            "/keys/1_sign.enc",
            "/keys/1_enc.enc",
            salt,
        )
    )
    db.commit()
    user_id = cursor.lastrowid

    # Initially not locked
    assert check_account_lockout(db, user_id) is False

    # 4 failed attempts: not locked yet
    for attempt in range(1, 5):
        count = record_failed_attempt(db, user_id)
        assert count == attempt
        assert check_account_lockout(db, user_id) is False

    # 5th failed attempt: reaches max_attempts (5) -> locked
    count = record_failed_attempt(db, user_id)
    assert count == 5
    assert check_account_lockout(db, user_id) is True

    # Check database state directly
    cursor.execute("SELECT is_locked, failed_login_attempts FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    assert row["is_locked"] == 1
    assert row["failed_login_attempts"] == 5

    # Successful login resets failed attempts and unlocks account
    reset_failed_attempts(db, user_id)
    assert check_account_lockout(db, user_id) is False

    cursor.execute("SELECT is_locked, failed_login_attempts FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    assert row["is_locked"] == 0
    assert row["failed_login_attempts"] == 0

def test_check_account_lockout_nonexistent_user(db):
    """Verify check_account_lockout returns False for nonexistent user."""
    assert check_account_lockout(db, 999999) is False
