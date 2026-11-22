import sqlite3
import pytest
from app.database.db import get_db, init_db

def test_database_initialization(app):
    """Verify that all required tables exist upon database initialization."""
    with app.app_context():
        init_db()
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert {'users', 'media', 'verification_history', 'audit_log'}.issubset(tables)

def test_foreign_key_enforcement(app):
    """Verify that foreign keys are enforced and prevent orphan media records."""
    with app.app_context():
        db = get_db()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("""
                INSERT INTO media (
                    media_id, owner_id, original_filename, file_type, file_size,
                    sha256_hash, phash, encrypted_file_path, wrapped_aes_key,
                    nonce, auth_tag, registration_manifest, digital_signature
                ) VALUES (
                    'nonexistent-media-id', 99999, 'test.jpg', 'image/jpeg', 1024,
                    'hash123', 'phash123', '/path/enc', X'00', X'00', X'00', '{}', X'00'
                )
            """)
            db.commit()

def test_role_check_constraint(app):
    """Verify that user role check constraint accepts valid roles and rejects invalid roles."""
    with app.app_context():
        db = get_db()
        # Invalid role should raise IntegrityError
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("""
                INSERT INTO users (
                    username, email, password_hash, totp_secret, role,
                    public_signing_key, public_encryption_key,
                    encrypted_signing_key_path, encrypted_encryption_key_path,
                    kdf_salt
                ) VALUES (
                    'badrole', 'bad@test.com', 'hash', 'totp', 'SuperUser',
                    'pubsign', 'pubenc', 'path1', 'path2', X'010203'
                )
            """)
            db.commit()

        # Valid role should succeed
        db.execute("""
            INSERT INTO users (
                username, email, password_hash, totp_secret, role,
                public_signing_key, public_encryption_key,
                encrypted_signing_key_path, encrypted_encryption_key_path,
                kdf_salt
            ) VALUES (
                'gooduser', 'good@test.com', 'hash', 'totp', 'User',
                'pubsign', 'pubenc', 'path1', 'path2', X'010203'
            )
        """)
        db.commit()
        
        cursor = db.execute("SELECT username, role FROM users WHERE username='gooduser'")
        row = cursor.fetchone()
        assert row['username'] == 'gooduser'
        assert row['role'] == 'User'

def test_standalone_init_db(tmp_path):
    """Verify init_db and get_db work properly outside Flask application context."""
    db_file = tmp_path / "standalone.db"
    init_db(db_path=str(db_file))
    
    conn = get_db(db_path=str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert {'users', 'media', 'verification_history', 'audit_log'}.issubset(tables)
    conn.close()
