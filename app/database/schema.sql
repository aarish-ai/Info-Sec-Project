-- MediaGuard Database Schema
-- Strict SQLite DDL with Foreign Keys, Check Constraints, and Cryptographic Fields

PRAGMA foreign_keys = ON;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    totp_secret TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'User' CHECK(role IN ('User', 'Auditor', 'Admin')),
    public_signing_key TEXT NOT NULL,
    public_encryption_key TEXT NOT NULL,
    encrypted_signing_key_path TEXT NOT NULL,
    encrypted_encryption_key_path TEXT NOT NULL,
    kdf_salt BLOB NOT NULL,
    is_locked INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Media Table
CREATE TABLE IF NOT EXISTS media (
    media_id TEXT PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    sha256_hash TEXT NOT NULL,
    phash TEXT NOT NULL,
    encrypted_file_path TEXT NOT NULL,
    wrapped_aes_key BLOB NOT NULL,
    nonce BLOB NOT NULL,
    auth_tag BLOB NOT NULL,
    registration_manifest TEXT NOT NULL,
    digital_signature BLOB NOT NULL,
    registration_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verification History Table
CREATE TABLE IF NOT EXISTS verification_history (
    verification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id TEXT NOT NULL REFERENCES media(media_id) ON DELETE CASCADE,
    verifier_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    uploaded_filename TEXT NOT NULL,
    submitted_sha256 TEXT NOT NULL,
    submitted_phash TEXT,
    hash_match INTEGER NOT NULL,
    signature_valid INTEGER NOT NULL,
    phash_distance INTEGER,
    overall_status TEXT NOT NULL,
    verification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cryptographic Audit Log Table (Hash-Chained)
CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    prev_hash TEXT NOT NULL,
    current_hash TEXT NOT NULL
);

-- Indexes for performance and lookup
CREATE INDEX IF NOT EXISTS idx_media_owner ON media(owner_id);
CREATE INDEX IF NOT EXISTS idx_media_sha256 ON media(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_verification_media ON verification_history(media_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
