from typing import Optional
import argon2
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from app.database.db import get_db

# Initialize Argon2id hasher with recommended security parameters
# Type 2 is Argon2id (default in argon2-cffi)
_hasher = argon2.PasswordHasher()

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using Argon2id with memory-hard parameters.
    Returns the Argon2 encoded hash string.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    return _hasher.hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    """
    Verifies a password against an Argon2id hash.
    Catches VerifyMismatchError, InvalidHashError, and VerificationError, returning False safely.
    """
    if not password_hash or not password:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False
    except Exception:
        return False

def _resolve_db_and_user_id(db_or_user_id, user_id: Optional[int] = None):
    """Support calling functions with (db, user_id) or just (user_id) defaulting to get_db()."""
    if user_id is None and isinstance(db_or_user_id, int):
        return get_db(), db_or_user_id
    db = db_or_user_id if db_or_user_id is not None else get_db()
    return db, user_id

def check_account_lockout(db, user_id: Optional[int] = None, max_attempts: int = 5) -> bool:
    """
    Checks if a user account is locked due to manual lockout or exceeding max failed login attempts.
    Returns True if locked, False otherwise.
    """
    database, uid = _resolve_db_and_user_id(db, user_id)
    if uid is None:
        return False

    cursor = database.cursor()
    cursor.execute("SELECT is_locked, failed_login_attempts FROM users WHERE user_id = ?", (uid,))
    row = cursor.fetchone()
    if not row:
        return False

    is_locked = bool(row["is_locked"])
    failed_attempts = row["failed_login_attempts"] or 0
    return is_locked or (failed_attempts >= max_attempts)

def record_failed_attempt(db, user_id: Optional[int] = None, max_attempts: int = 5) -> int:
    """
    Increments failed_login_attempts for the user.
    If attempts reach max_attempts (default 5), escalates by setting is_locked = 1.
    Commits changes and returns the new failed attempts count.
    """
    database, uid = _resolve_db_and_user_id(db, user_id)
    if uid is None:
        return 0

    cursor = database.cursor()
    cursor.execute("SELECT failed_login_attempts, is_locked FROM users WHERE user_id = ?", (uid,))
    row = cursor.fetchone()
    if not row:
        return 0

    current_attempts = row["failed_login_attempts"] or 0
    new_attempts = current_attempts + 1
    new_is_locked = 1 if (new_attempts >= max_attempts or row["is_locked"]) else 0

    cursor.execute(
        "UPDATE users SET failed_login_attempts = ?, is_locked = ? WHERE user_id = ?",
        (new_attempts, new_is_locked, uid)
    )
    database.commit()
    return new_attempts

def reset_failed_attempts(db, user_id: Optional[int] = None) -> None:
    """
    Resets failed_login_attempts to 0 and unlocks the account (is_locked = 0)
    upon successful authentication. Commits changes.
    """
    database, uid = _resolve_db_and_user_id(db, user_id)
    if uid is None:
        return

    cursor = database.cursor()
    cursor.execute(
        "UPDATE users SET failed_login_attempts = 0, is_locked = 0 WHERE user_id = ?",
        (uid,)
    )
    database.commit()
