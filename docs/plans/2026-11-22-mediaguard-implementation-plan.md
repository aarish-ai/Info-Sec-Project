# MediaGuard – Secure Media Authenticity & Integrity Verification System
# Master Implementation Plan (Path A: Staged Subagent Hierarchy)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> **Orchestration Model:** Staged Subagent Hierarchy with Ruthless Adversarial Review Gates. Each major phase is implemented by a specialized Author Subagent and must be approved by an independent Adversarial Reviewer Subagent before merging.

**Goal:** Build a complete, production-grade, secure media authenticity and integrity verification system (MediaGuard) featuring dual RSA key pairs, AES-256-GCM envelope encryption, streamed SHA-256 and pHash verification, signed PDF certificates with QR codes, a universal public verification portal, hash-chained tamper-evident audit logs, and an administrative `SECURE_MODE` switch demonstrating 8 OWASP Top 10 vulnerabilities before and after.

**Architecture:** Modular Python 3.11+ application using Flask with Jinja2 server-side rendering, SQLite3 relational persistence, and the Python `cryptography` hazmat library. Strictly follows the Key Separation Principle, Zero-Plaintext Storage policy, and defensive HTTP headers.

**Tech Stack:** Python 3.11+, Flask 3.0+, Jinja2, SQLite3, `cryptography` (AES-GCM, RSA-PSS, RSA-OAEP, scrypt), `argon2-cffi`, `hashlib`, `imagehash`, `Pillow`, `pyotp`, `qrcode`, `reportlab`, `pytest`, `pip-audit`.

## Global Constraints
- Target Directory: `d:/Projects/Unii/IS Project/`
- Zero Plaintext Retention: Temporary unencrypted media files must be permanently deleted immediately after AES-256-GCM encryption and manifest signing.
- Key Separation Principle: Never reuse the same RSA key for both digital signatures and encryption wrapping.
- Zero Hardcoded Localhost: Relative paths must be used for frontend assets and internal API endpoints.
- No Inline Styles: All frontend templates must strictly use design tokens from `variables.css` and component classes from `style.css` to prevent "vibecoded" inconsistencies.
- Parameterized Queries: All database interactions must use parameterized SQL (`?` placeholders) to prevent SQL injection.
- Security Headers: CSP, X-Frame-Options, X-Content-Type-Options, and secure cookie attributes (`HttpOnly`, `SameSite=Strict`) must be enforced globally.

---

## Subagent Hierarchy & Adversarial Review Protocol (Path A Architecture)

This implementation strictly adheres to the **CTO-Led Staged Subagent Hierarchy** to ensure zero cryptographic bugs, zero access control leaks, and a 100% cohesive, non-"vibecoded" frontend.

```
                              [ CTO / ORCHESTRATOR ] (Antigravity Coordinator)
                                       |
    +----------------------------------+----------------------------------+
    |                                  |                                  |
    v                                  v                                  v
[ POD 1: CRYPTO & CORE BACKEND ]   [ POD 2: FRONTEND ARCHITECTURE ]   [ POD 3: ATTACK & VIVA DEMO ]
- Author: Backend-Crypto-Dev       - Author: Frontend-Design-Dev      - Author: Integration-Exploit-Dev
- Reviewer: Ruthless-Crypto-Auditor- Reviewer: UI-Consistency-Auditor - Reviewer: Penetration-Auditor
                                       |
                                       +----------------------------------+
                                       |
                                       v
                        [ POD 4: REAL-BROWSER E2E QA ]
                        - Reviewer: Browser-Automation-QA-Auditor
                        - Mechanism: Built-in Native Browser & Chrome DevTools MCP
```

### Pod Roles & Persona Mandates:

1. **CTO / Orchestrator (Antigravity Coordinator):**
   - Owns the master plan, manages task sequencing, resolves cross-pod dependencies, inspects handoffs, and enforces quality gates before advancing phases.

2. **Pod 1: Backend, Cryptography & Identity Pod**
   - **Author (`Backend-Crypto-Dev`):** Implements cryptographic primitives (`hashing.py`, `key_management.py`, `signatures.py`, `ciphers.py`), database schemas (`schema.sql`, `db.py`), and authentication (`auth_manager.py`, `totp_manager.py`). Strictly writes tests first (TDD).
   - **Reviewer (`Ruthless-Crypto-Auditor`):** Persona: *"A senior cryptographic auditor whose pay depends on finding every flaw, edge case, and vulnerability."* Specifically inspects nonces, key separation, authenticated decryption tags, and scrypt/Argon2id parameters.

3. **Pod 2: Frontend Architecture & UI Design Pod**
   - **Author (`Frontend-Design-Dev`):** Establishes the design tokens (`variables.css`), base layout (`base.html`), component classes (`style.css`), and templates for all features.
   - **Reviewer (`UI-Consistency-Auditor`):** Persona: *"An uncompromising Design Director dedicated to eliminating AI-generated 'vibecoding' and visual slop."* Enforces zero inline styles, strict token usage, and layout harmony.

4. **Pod 3: Full-Stack Integration, Attack Simulation & Viva Pod**
   - **Author (`Integration-Exploit-Dev`):** Wires the end-to-end Flask routes, PDF certificate generator, hash-chained audit engine, attack simulations, and the `SECURE_MODE` toggle.
   - **Reviewer (`Penetration-Auditor`):** Persona: *"An adversarial security pentester testing for grading evaluation."* Attacks IDOR, checks audit chains, verifies `SECURE_MODE` dual states, and runs `pytest` and `pip-audit`.

5. **Pod 4: Live Real-Browser End-to-End QA Pod**
   - **Reviewer (`Browser-Automation-QA-Auditor`):** Persona: *"A meticulous QA Automation & User Experience Auditor who never assumes code works without seeing it in a real browser."*
     - Uses Antigravity's **built-in webview browser subagent** and **Chrome DevTools MCP** (`navigate_page`, `click`, `fill`, `take_screenshot`).
     - Boots the local Flask server on a test port.
     - Physically clicks through every user flow: registers account, enters 2FA TOTP code, uploads genuine media, downloads PDF certificate, opens public verify portal, uploads tampered image, verifies red alert cards, inspects audit logs, and captures real screenshots for Ms. Hirra Anwar's 5-7 page report.

### The Handover & Review Protocol (The "No Mercy" Rule):
1. **Author Completes Work:** The Author subagent implements the assigned task using Test-Driven Development (TDD), runs tests, and submits a completion report with test outputs.
2. **Reviewer Independent Audit:** The CTO dispatches the independent Reviewer Subagent with the diff, test suite, and the specific checklist for that module.
3. **Rejection or Sign-Off Loop:**
   - If the Reviewer finds *any* cryptographic flaw, timing leak, missing test case, or "vibecoded" styling inconsistency: **The Reviewer rejects the submission**, names the exact defect, and provides specific remediation instructions.
   - The Author subagent is re-engaged to fix the defect.
   - The Reviewer re-audits.
   - Only when the Reviewer signs off with *"APPROVED: ZERO DEFECTS"* does the CTO mark the phase complete and unlock the next phase.

---

## File Structure & Module Responsibilities

```
d:/Projects/Unii/IS Project/
├── requirements.txt                 # Pinned dependencies
├── config.py                        # Centralized app configuration & SECURE_MODE switch
├── run.py                           # Application entry point
│
├── app/
│   ├── __init__.py                  # Flask app factory, security middleware & error handlers
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.sql               # SQLite DDL: users, media, verification_history, audit_log
│   │   └── db.py                    # Connection context manager & parameterized query helpers
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── hashing.py               # Streamed SHA-256 and pHash calculations
│   │   ├── key_management.py        # Dual RSA keygen, scrypt KDF, AES-GCM private key storage
│   │   ├── signatures.py            # Canonical JSON manifest builder, RSA-PSS sign & verify
│   │   ├── ciphers.py               # AES-256-GCM envelope encryption/decryption, RSA-OAEP wrapping
│   │   ├── certificate.py           # ReportLab PDF certificate generation with dynamic QR
│   │   ├── audit_chain.py           # Cryptographic hash chaining for tamper-evident logs
│   │   ├── auth_manager.py          # Argon2id password hashing, lockout logic, RBAC decorators
│   │   ├── totp_manager.py          # RFC 6238 TOTP generation & verification via pyotp
│   │   └── validators.py            # File size cap, magic-byte MIME sniffing, secure filenames
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                  # Register, Login, 2FA setup/verify, Logout
│   │   ├── media.py                 # Media upload, user library, secure download stream
│   │   ├── verify.py                # Public verification portal & detailed verdict renderer
│   │   ├── audit.py                 # Audit log viewer & 1-click chain integrity verifier
│   │   ├── admin.py                 # User management, account unlocker & SECURE_MODE toggle
│   │   └── experiments.py           # Attack simulation UI & interactive test endpoints
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── variables.css        # Design tokens: palette, typography scale, radii, shadows
│   │   │   └── style.css            # Component library: cards, badges, buttons, terminal tables
│   │   └── js/
│   │       └── main.js              # Client-side validation & toast alerts
│   │
│   └── templates/
│       ├── base.html                # Master layout with navbar, alerts, CSRF & security headers
│       ├── index.html               # Landing page with hero banner & metric stats
│       ├── auth/
│       │   ├── login.html           # Login form with failed attempt lockout counter
│       │   ├── register.html        # Registration form
│       │   └── setup_2fa.html       # TOTP QR code display & confirmation input
│       ├── media/
│       │   ├── upload.html          # Drag-and-drop upload form
│       │   └── library.html         # User gallery, certificate downloads & retrieve buttons
│       ├── verify/
│       │   ├── verify.html          # Universal public verification upload form
│       │   └── result.html          # Color-coded verdict card & pHash diagnostics
│       ├── audit/
│       │   └── audit_log.html       # Immutable audit table & "Verify Chain" action
│       ├── admin/
│       │   ├── dashboard.html       # User accounts & lockout statuses
│       │   └── secure_mode.html     # Live Before-and-After OWASP toggle demonstrator
│       └── experiments/
│           └── simulations.html     # 6 interactive attack simulations
│
├── storage/                         # Protected filesystem storage
│   ├── encrypted_media/             # AES-256-GCM ciphertexts (*.enc)
│   └── key_storage/                 # Password-encrypted private key PEMs (*.enc)
│
├── experiments/
│   ├── __init__.py
│   └── attack_simulations.py        # Standalone CLI attack scripts for viva demos
│
└── tests/
    ├── __init__.py
    ├── conftest.py                  # Pytest fixtures: temp database, client, dummy keys
    ├── test_crypto.py               # Unit tests: SHA-256, pHash, AES-GCM, RSA-PSS, RSA-OAEP
    ├── test_auth.py                 # Unit tests: Argon2id, scrypt, TOTP, lockout, RBAC
    ├── test_audit_chain.py          # Unit tests: Hash chaining & tamper detection
    ├── test_routes.py               # Integration tests: Endpoints, CSRF, IDOR check
    └── test_secure_mode.py          # Dual-state tests: Weakness in False, Defense in True
```

---

## Phase 1: Environment, Configuration & Database Engine

### Task 1: Environment & Dependency Setup
**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `storage/encrypted_media/.gitkeep`
- Create: `storage/key_storage/.gitkeep`

**Interfaces:**
- Produces: `config.Config` class holding secret keys, storage paths, and the dynamic `SECURE_MODE` flag.

- [ ] **Step 1: Write requirements.txt with pinned dependencies**
```text
Flask>=3.0.0
cryptography>=42.0.0
argon2-cffi>=23.1.0
pyotp>=2.9.0
qrcode>=7.4.2
imagehash>=4.3.1
Pillow>=10.2.0
reportlab>=4.1.0
pytest>=8.0.0
pip-audit>=2.7.0
```

- [ ] **Step 2: Create storage directories**
Create directories `storage/encrypted_media` and `storage/key_storage`.

- [ ] **Step 3: Implement config.py**
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mediaguard-dev-secret-key-change-in-prod')
    DATABASE_PATH = BASE_DIR / 'app' / 'database' / 'mediaguard.db'
    ENCRYPTED_MEDIA_DIR = BASE_DIR / 'storage' / 'encrypted_media'
    KEY_STORAGE_DIR = BASE_DIR / 'storage' / 'key_storage'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB Cap
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'mov'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'video/mp4', 'video/quicktime'
    }
    # Dynamic demonstration switch for OWASP Top 10 Before/After viva demo
    SECURE_MODE = True
```

- [ ] **Step 4: Verify dependencies install cleanly**
Run: `pip install -r requirements.txt`
Expected: Successfully installed packages without conflicts.

---

### Task 2: Database Schema & Connection Context Manager
**Files:**
- Create: `app/database/schema.sql`
- Create: `app/database/db.py`
- Test: `tests/test_database.py`

**Interfaces:**
- Produces: `get_db()`, `init_db(app)` providing safe SQLite connection with foreign keys enabled and row-factory support.

- [ ] **Step 1: Write tests/test_database.py**
```python
import sqlite3
from app.database.db import get_db, init_db

def test_database_initialization(app):
    with app.app_context():
        init_db()
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert {'users', 'media', 'verification_history', 'audit_log'}.issubset(tables)
```

- [ ] **Step 2: Implement app/database/schema.sql**
Define table DDL for `users`, `media`, `verification_history`, and `audit_log` with all required cryptographic and provenance columns.

- [ ] **Step 3: Implement app/database/db.py**
Implement thread-safe connection handling using Flask's `g` object, enabling `PRAGMA foreign_keys = ON;` and `sqlite3.Row`.

- [ ] **Step 4: Run database tests**
Run: `pytest tests/test_database.py -v`
Expected: PASS

---

## Phase 2: Core Cryptographic Engines (Key Separation & Primitives)

### Task 3: Streamed Hashing & Perceptual Hashing Engine
**Files:**
- Create: `app/core/hashing.py`
- Test: `tests/test_hashing.py`

**Interfaces:**
- Produces:
  - `compute_streamed_sha256(file_path_or_stream) -> str` (64-char hex)
  - `compute_phash(file_path_or_stream) -> str` (16-char hex)
  - `compute_phash_distance(hash1_hex: str, hash2_hex: str) -> int` (Hamming distance)

- [ ] **Step 1: Write tests/test_hashing.py**
Test SHA-256 accuracy, streamed chunking consistency, pHash generation for images, and graceful handling/sentinel return for video formats where pHash does not apply.

- [ ] **Step 2: Implement app/core/hashing.py**
Implement 64KB chunk-streamed SHA-256 to ensure low memory consumption. Integrate `imagehash.phash` via `Pillow` with Hamming distance bit-count logic.

- [ ] **Step 3: Run hashing tests**
Run: `pytest tests/test_hashing.py -v`
Expected: PASS

---

### Task 4: Dual RSA Key Management & Password KDF
**Files:**
- Create: `app/core/key_management.py`
- Test: `tests/test_key_management.py`

**Interfaces:**
- Produces:
  - `generate_user_key_pairs() -> dict` (Generates separate Signing and Encryption RSA-2048/3072 key pairs)
  - `derive_kek(password: str, salt: bytes) -> bytes` (scrypt KDF returning 32-byte key)
  - `encrypt_private_key(private_pem: bytes, kek: bytes) -> tuple[bytes, bytes, bytes]` (AES-GCM encrypt: ciphertext, nonce, tag)
  - `decrypt_private_key(encrypted_pem: bytes, nonce: bytes, tag: bytes, kek: bytes) -> bytes`

- [ ] **Step 1: Write tests/test_key_management.py**
Verify that two distinct RSA key pairs are produced (strict key separation), verify scrypt key derivation consistency, and verify AES-GCM encrypted private key round-trip decryption.

- [ ] **Step 2: Implement app/core/key_management.py**
Implement RSA key generation using 65537 public exponent, `scrypt` KDF ($N=2^{14}, r=8, p=1$), and AES-256-GCM authenticated encryption for private key serialization.

- [ ] **Step 3: Run key management tests**
Run: `pytest tests/test_key_management.py -v`
Expected: PASS

---

### Task 5: Canonical Manifest Builder & RSA-PSS Digital Signatures
**Files:**
- Create: `app/core/signatures.py`
- Test: `tests/test_signatures.py`

**Interfaces:**
- Produces:
  - `build_canonical_manifest(media_id, owner_id, filename, file_size, mime_type, sha256_hash, phash, timestamp_utc) -> str`
  - `sign_manifest(canonical_manifest: str, private_signing_key_pem: bytes) -> bytes` (RSA-PSS with SHA-256)
  - `verify_manifest_signature(canonical_manifest: str, signature: bytes, public_signing_key_pem: str) -> bool`

- [ ] **Step 1: Write tests/test_signatures.py**
Test deterministic JSON ordering (`sort_keys=True`), valid signature verification, and test that changing even a single byte or timestamp in the manifest causes `verify_manifest_signature` to return `False`.

- [ ] **Step 2: Implement app/core/signatures.py**
Use `cryptography.hazmat.primitives.asymmetric.padding.PSS` with `MGF1(hashes.SHA256())` and maximum salt length.

- [ ] **Step 3: Run signature tests**
Run: `pytest tests/test_signatures.py -v`
Expected: PASS

---

### Task 6: Symmetric Envelope Encryption & Decryption
**Files:**
- Create: `app/core/ciphers.py`
- Test: `tests/test_ciphers.py`

**Interfaces:**
- Produces:
  - `encrypt_media_envelope(file_bytes: bytes, owner_public_enc_key_pem: str) -> dict` (Returns `ciphertext`, `wrapped_aes_key`, `nonce`, `auth_tag`)
  - `decrypt_media_envelope(ciphertext: bytes, wrapped_aes_key: bytes, nonce: bytes, auth_tag: bytes, owner_private_enc_key_pem: bytes) -> bytes`

- [ ] **Step 1: Write tests/test_ciphers.py**
Test full encrypt/decrypt round-trip on binary payloads, verify that corrupting the authentication tag raises `InvalidTag`, and verify that attempting to unwrap the AES key with a different user's private key fails.

- [ ] **Step 2: Implement app/core/ciphers.py**
Generate fresh random 256-bit AES key and 96-bit nonce per file. Use AES-GCM for media and RSA-OAEP with SHA-256 and MGF1 for key wrapping.

- [ ] **Step 3: Run cipher tests**
Run: `pytest tests/test_ciphers.py -v`
Expected: PASS

---

### Task 7: Crypto Engine Review Gate (Adversarial Security Review)
- [ ] **Action:** Dispatch the **Adversarial Crypto Reviewer Subagent** to audit `hashing.py`, `key_management.py`, `signatures.py`, and `ciphers.py`.
- [ ] **Checklist:**
  - Verify zero nonce reuse vulnerability.
  - Verify strict separation between signing and encryption keys.
  - Verify that ciphertext tampering is rejected before any plaintext is released.
  - Run full crypto test suite: `pytest tests/test_crypto.py tests/test_hashing.py tests/test_signatures.py tests/test_ciphers.py -v`.
  - Fix any identified issues before moving to Phase 3.

---

## Phase 3: Authentication, RBAC & Session Security

### Task 8: Argon2id Password Hashing & Account Lockout
**Files:**
- Create: `app/core/auth_manager.py`
- Test: `tests/test_auth_manager.py`

**Interfaces:**
- Produces:
  - `hash_password(password: str) -> str`
  - `verify_password(password_hash: str, password: str) -> bool`
  - `check_account_lockout(user_id: int) -> bool`
  - `record_failed_attempt(user_id: int) -> int`
  - `reset_failed_attempts(user_id: int)`

- [ ] **Step 1: Write tests/test_auth_manager.py**
Test Argon2id hashing and verification, test lockout trigger after 5 consecutive failed attempts, and verify reset on successful authentication.

- [ ] **Step 2: Implement app/core/auth_manager.py**
Implement `argon2.PasswordHasher` with recommended time and memory parameters, and database-backed lockout tracking.

- [ ] **Step 3: Run auth manager tests**
Run: `pytest tests/test_auth_manager.py -v`
Expected: PASS

---

### Task 9: TOTP Multi-Factor Authentication
**Files:**
- Create: `app/core/totp_manager.py`
- Test: `tests/test_totp.py`

**Interfaces:**
- Produces:
  - `generate_totp_secret() -> str`
  - `get_totp_uri(username: str, secret: str) -> str`
  - `generate_totp_qr_png(uri: str) -> bytes`
  - `verify_totp_code(secret: str, code: str) -> bool`

- [ ] **Step 1: Write tests/test_totp.py**
Test RFC 6238 time-step verification with `pyotp.TOTP`, test rejection of invalid codes, and test QR code byte generation.

- [ ] **Step 2: Implement app/core/totp_manager.py**
Integrate `pyotp` and `qrcode` to generate provisioning URIs and PNG buffers.

- [ ] **Step 3: Run TOTP tests**
Run: `pytest tests/test_totp.py -v`
Expected: PASS

---

### Task 10: Flask App Factory, Security Headers & CSRF
**Files:**
- Create: `app/__init__.py`
- Modify: `run.py`
- Test: `tests/test_security_headers.py`

**Interfaces:**
- Produces: `create_app()` factory with Content Security Policy, strict session cookies, and generic error handlers.

- [ ] **Step 1: Implement security headers middleware in app/__init__.py**
Enforce `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`, and session cookie parameters (`SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Strict'`).

- [ ] **Step 2: Implement run.py**
Provide standard CLI runner: `app = create_app(); app.run(port=5000)`.

- [ ] **Step 3: Run security header tests**
Run: `pytest tests/test_security_headers.py -v`
Expected: PASS

---

### Task 11: Authentication Routes & Role-Based Access Control (RBAC)
**Files:**
- Create: `app/routes/auth.py`
- Test: `tests/test_auth_routes.py`

**Interfaces:**
- Routes: `/auth/register` (GET/POST), `/auth/setup-2fa` (GET/POST), `/auth/login` (GET/POST), `/auth/logout` (POST)
- Decorators: `@login_required`, `@require_role('Admin')`, `@require_role('Auditor')`

- [ ] **Step 1: Write integration tests for registration and login flows**
Test successful registration, 2FA setup, login with valid credentials + TOTP, rejection of invalid password, and lockout enforcement after 5 failed tries.

- [ ] **Step 2: Implement app/routes/auth.py**
Connect forms to Argon2id, key generation pipeline, and session dictionary.

- [ ] **Step 3: Run auth route tests**
Run: `pytest tests/test_auth_routes.py -v`
Expected: PASS

---

### Task 12: Auth & Access Control Review Gate
- [ ] **Action:** Dispatch **Security Reviewer Subagent** to audit session handling, password storage, and RBAC enforcement.
- [ ] **Checklist:**
  - Verify that private keys on disk are never decrypted without valid user credentials.
  - Verify that regular users cannot access Auditor or Admin routes.
  - Confirm lockout persists across sessions.

---

## Phase 4: Frontend Design System & Master Templates (Anti-Vibecoding Gate)

### Task 13: CSS Design Tokens & Component Stylesheet
**Files:**
- Create: `app/static/css/variables.css`
- Create: `app/static/css/style.css`

**Interfaces:**
- Produces: Cohesive design tokens and unified component classes (`.card-glass`, `.badge-status`, `.btn-primary`, `.btn-danger`, `.table-vault`, `.input-terminal`).

- [ ] **Step 1: Implement app/static/css/variables.css**
Define semantic color palette: slate backgrounds (`--bg-base: #0b0f19`, `--bg-surface: #111827`, `--bg-elevated: #1e293b`), indigo primary (`--primary: #6366f1`), emerald success (`--success: #10b981`), rose danger (`--danger: #f43f5e`), amber warning (`--warning: #f59e0b`), typography scale, and spacing tokens.

- [ ] **Step 2: Implement app/static/css/style.css**
Implement modern dark-mode component styling: glassmorphism panels, high-contrast monospace badges for hashes and keys, responsive flex/grid layouts, and clean button states.

---

### Task 14: Master Base Template & Responsive Shell
**Files:**
- Create: `app/templates/base.html`
- Create: `app/templates/index.html`

**Interfaces:**
- Produces: Unified layout extended by all child templates, featuring dynamic navigation (guest vs. authenticated roles), flash message banners, and CSRF token injection.

- [ ] **Step 1: Implement app/templates/base.html**
Write semantic HTML5 layout with dark-mode container, navigation bar, role indicators, and flash alert toasts.

- [ ] **Step 2: Implement app/templates/index.html**
Write high-impact landing page with project mission, metrics counter, and direct action buttons for Public Verification and Portal Login.

---

### Task 15: Authentication & Account Templates
**Files:**
- Create: `app/templates/auth/login.html`
- Create: `app/templates/auth/register.html`
- Create: `app/templates/auth/setup_2fa.html`

- [ ] **Step 1: Implement auth templates matching design tokens**
Ensure form controls, lockout alert banners, and the TOTP QR display use the standardized `.card-glass` and `.btn-primary` classes.

---

### Task 16: UI Consistency Review Gate
- [ ] **Action:** Dispatch the **UI/UX Design Reviewer Subagent** to audit `base.html`, `index.html`, and auth templates.
- [ ] **Checklist:**
  - Verify zero custom inline CSS (`style="..."`).
  - Verify WCAG AA contrast on all text and badge elements.
  - Verify responsive rendering on mobile and desktop viewports.

---

## Phase 5: Media Registration, Certificate Generation & Secure Retrieval

### Task 17: Upload Validation & Magic Bytes Sniffer
**Files:**
- Create: `app/core/validators.py`
- Test: `tests/test_validators.py`

**Interfaces:**
- Produces: `validate_upload(file_storage) -> tuple[bool, str]` (Validates 50MB size cap, checks extension, and verifies true MIME type using magic bytes).

- [ ] **Step 1: Implement app/core/validators.py**
Implement header sniffing for JPEG (`FF D8 FF`), PNG (`89 50 4E 47`), MP4 (`ftyp`), and QuickTime MOV.

- [ ] **Step 2: Test validation with genuine and spoofed files**
Run: `pytest tests/test_validators.py -v`
Expected: PASS

---

### Task 18: PDF Verification Certificate Generator with Dynamic QR
**Files:**
- Create: `app/core/certificate.py`
- Test: `tests/test_certificate.py`

**Interfaces:**
- Produces: `generate_verification_certificate_pdf(media_record: dict, base_url: str) -> bytes`

- [ ] **Step 1: Implement app/core/certificate.py**
Use `reportlab.platypus` to assemble an official, elegant Certificate of Provenance containing Media ID, owner, registration timestamp, SHA-256 fingerprint, pHash, and a dynamic QR code pointing to the public verification endpoint.

- [ ] **Step 2: Verify PDF binary output**
Run: `pytest tests/test_certificate.py -v`
Expected: PASS

---

### Task 19: Media Routes, Zero-Plaintext Pipeline & Retrieval
**Assigned Author:** Pod 3: Integration-Exploit-Dev
**Files:**
- Create: `app/routes/media.py`
- Create: `app/templates/media/upload.html`
- Create: `app/templates/media/library.html`
- Create: `app/templates/media/preview.html`
- Test: `tests/test_media_routes.py`

**Interfaces:**
- Routes: `/media` (GET), `/media/upload` (GET/POST), `/media/<media_id>/download` (GET), `/media/<media_id>/certificate` (GET), `/media/<media_id>/preview` (GET)
- Retrieval Rule: In-browser visual rendering (`/preview`) is reserved strictly for images (JPG/PNG). For all video formats (MP4/MOV), the interface provides direct authenticated streaming download links (`/download`) with proper `Content-Disposition: attachment`.

- [ ] **Step 1: Write integration tests for upload and retrieval**
Test that uploading encrypts the file, deletes the unencrypted temporary upload immediately, saves the record in SQLite, and allows only the owner to download the decrypted original. Confirm non-owners receive 403 Forbidden.

- [ ] **Step 2: Implement app/routes/media.py and templates**
Wire upload form, envelope encryption pipeline, zero-plaintext deletion, and authenticated in-memory decryption stream for download. Implement image preview rendering for JPG/PNG and direct authenticated download for MP4/MOV.

- [ ] **Step 3: Run media route tests**
Run: `pytest tests/test_media_routes.py -v`
Expected: PASS

---

## Phase 6: Universal Public Verification Portal

### Task 20: Public Verification Engine & Endpoint
**Files:**
- Create: `app/routes/verify.py`
- Create: `app/templates/verify/verify.html`
- Create: `app/templates/verify/result.html`
- Test: `tests/test_verify_routes.py`

**Interfaces:**
- Routes: `/verify` (GET/POST)
- Outcomes: `AUTHENTIC`, `MODIFIED`, `INVALID_SIGNATURE`, `UNKNOWN`

- [ ] **Step 1: Write tests for all 4 verification outcomes**
Test genuine file matching manifest (Authentic), modified file with differing hash (Modified with pHash score), corrupted signature (Invalid Signature), and nonexistent Media ID (Unknown).

- [ ] **Step 2: Implement app/routes/verify.py and result templates**
Implement dual-check verification: Compare uploaded SHA-256 against manifest, verify RSA-PSS signature over manifest using owner's public key, and compute pHash Hamming distance diagnostic.

- [ ] **Step 3: Run verify route tests**
Run: `pytest tests/test_verify_routes.py -v`
Expected: PASS

---

## Phase 7: Hash-Chained Audit Trail & Compliance

### Task 21: Cryptographic Hash-Chaining Engine
**Files:**
- Create: `app/core/audit_chain.py`
- Test: `tests/test_audit_chain.py`

**Interfaces:**
- Produces:
  - `append_audit_log(user_id, action, details, ip_address) -> int`
  - `verify_audit_chain() -> tuple[bool, int, str]` (Validates entire chain, returns first corrupted index if invalid)

- [x] **Step 1: Write tests/test_audit_chain.py**
Test successive hash linkages (`current_hash = SHA-256(prev_hash + data)`), verify that manual modification of a database row causes `verify_audit_chain()` to fail and report the exact corrupted row index.

- [x] **Step 2: Implement app/core/audit_chain.py**
Implement blockchain-style linkage on the `audit_log` SQLite table with genesis block handling.

- [x] **Step 3: Run audit chain tests**
Run: `pytest tests/test_audit_chain.py -v`
Expected: PASS

---

### Task 22: Auditor Route & UI Dashboard
**Files:**
- Create: `app/routes/audit.py`
- Create: `app/templates/audit/audit_log.html`

**Interfaces:**
- Routes: `/audit` (GET), `/audit/verify-chain` (POST) — Restricted to Auditor and Admin roles.

- [x] **Step 1: Implement audit log viewer and interactive chain verification button**
Render the immutable log table and wire the AJAX/form endpoint returning chain integrity status.

---

## Phase 8: Attack Simulations, `SECURE_MODE` Switch & Viva Verification

### Task 23: Security Attack Simulation Suite
**Files:**
- Create: `experiments/attack_simulations.py`
- Create: `app/routes/experiments.py`
- Create: `app/templates/experiments/simulations.html`
- Test: `tests/test_simulations.py`

**Interfaces:**
- 6 Attacks:
  1. Image Byte & Pixel Modification
  2. File Replacement Attack
  3. Digital Signature Tampering
  4. Wrong-Key Verification Attack
  5. Unauthorized Decryption / Key Mismatch
  6. Encrypted File Tampering (Ciphertext Bit-Flipping)

- [x] **Step 1: Implement experiments/attack_simulations.py**
Write standalone reproducible Python functions for all 6 attacks.

- [x] **Step 2: Wire web UI demonstrator at /experiments**
Allow evaluators to trigger any of the 6 attacks with one click and observe the cryptographic defense.

- [x] **Step 3: Run attack simulation tests**
Run: `pytest tests/test_simulations.py -v`
Expected: PASS

---

### Task 24: `SECURE_MODE` Switch & Admin Demonstration Dashboard
**Files:**
- Create: `app/routes/admin.py`
- Create: `app/templates/admin/dashboard.html`
- Create: `app/templates/admin/secure_mode.html`
- Test: `tests/test_secure_mode.py`

**Interfaces:**
- Switch: `config.Config.SECURE_MODE = True/False`
- Covers 8 OWASP Top 10 categories with explicit dual-branch execution:
  - A01: Broken Access Control (IDOR bypass in False vs. 403 Forbidden in True)
  - A02: Cryptographic Failures (Plaintext storage in False vs. AES-GCM envelope in True)
  - A03: Injection (Raw SQL in False vs. Parameterized queries in True)
  - A04: Insecure Design (No size limits in False vs. 50MB cap in True)
  - A05: Security Misconfiguration (Debug tracebacks in False vs. Safe error handlers in True)
  - A06: Vulnerable Components (pip-audit check)
  - A07: Authentication Failures (Unlimited attempts in False vs. 5-attempt lockout in True)
  - A08: Integrity Failures (Silent acceptance in False vs. SHA-256 + RSA-PSS check in True)

- [x] **Step 1: Write tests verifying both states of SECURE_MODE**
Verify that switching `SECURE_MODE = False` exposes the expected vulnerability and `SECURE_MODE = True` activates the defense.

- [x] **Step 2: Implement app/routes/admin.py and secure_mode.html**
Build the administrative toggle and real-time status matrix for classroom viva presentations.

- [x] **Step 3: Run secure mode tests**
Run: `pytest tests/test_secure_mode.py -v`
Expected: PASS

---

### Task 25: Full-Stack Penetration & Final System Audit Gate
- [x] **Action:** Dispatch the **Lead Adversarial Reviewer Subagent** to audit the entire repository.
- [x] **Checklist:**
  - Run complete test suite: `pytest -v` (100% pass rate required).
  - Run security dependency audit: `pip-audit`.
  - Perform code-level walkthrough of all 6 viva demonstration steps from [Idea.md](file:///d:/Projects/Unii/IS%20Project/Idea.md).
  - Confirm zero broken links, zero console errors, and zero "vibecoded" styling inconsistencies.

---

### Task 26: Real-Browser End-to-End Live QA & Evidence Capture
- [ ] **Action:** Dispatch **Pod 4: `Browser-Automation-QA-Auditor` Subagent** using Antigravity's **built-in webview browser** and **Chrome DevTools MCP** (`navigate_page`, `fill`, `click`, `take_screenshot`).
- [ ] **Live End-to-End Walkthrough Steps:**
  1. Boot the live Flask server: `python run.py`.
  2. Navigate to `http://127.0.0.1:5000/` and verify landing page aesthetics and metrics.
  3. Register a test user account (`/auth/register`), scan/enter the 2FA TOTP code, and verify session persistence.
  4. Upload an authentic image via drag-and-drop (`/media/upload`), verify envelope encryption, download the PDF verification certificate, and confirm plaintext is erased.
  5. Open an incognito session, navigate to the public verification portal (`/verify`), upload the authentic file with Certificate ID, and verify the **Green "AUTHENTIC"** verdict card.
  6. Upload a tampered test image against the same Certificate ID, and verify the **Red "MODIFIED"** alert card with pHash visual similarity scores.
  7. Log in as Auditor (`/audit`), inspect the tamper-evident table, and click **"Verify Entire Audit Chain"** to confirm zero corrupted blocks.
  8. Log in as Admin (`/admin`), toggle `SECURE_MODE` from True to False, test the IDOR vulnerability, toggle back to True, and confirm 403 Forbidden.
  9. Capture and save high-resolution screenshots to `docs/evidence/` for Ms. Hirra Anwar's 5-7 page final report.
  10. Assert zero console errors, zero broken layouts, and zero failed requests.

---
*End of Master Implementation Plan — Prepared for NUST SEECS CS-353 Information Security Semester Project.*
