# Stream B Brief: Identity Provisioning & Vault Storage (Tasks 5 & 6)

**Repository Path:** `d:\Projects\Unii\IS Project`
**Templates to Redesign:**
- `app/templates/auth/login.html` (Task 5)
- `app/templates/auth/register.html` (Task 5)
- `app/templates/auth/setup_2fa.html` (Task 5)
- `app/templates/media/upload.html` (Task 6)
- `app/templates/media/library.html` (Task 6)
- `app/templates/media/preview.html` (Task 6)

**Requirements for Task 5 (Auth & 2FA):**
1. `auth/login.html`:
   - Style as the **Vault Credential Access Terminal** with chamfered housing and command aperture inputs (`usr:`, `pwd:`, `totp:`).
   - Retain form names `username`, `password`, `totp_code`, button text `'Authenticate & Unlock Vault'`, and class `'card-glass'` to satisfy `test_login_page_renders_clean_form`.
   - Add lockout telemetry alert box displaying failed attempt count (`[ATTEMPTS: 3 / 5]`).
2. `auth/register.html`:
   - Style as the **Identity Provisioning Chamber**. Remove redundant card-in-card nesting.
   - Add real-time **Keypair Provisioning Readout**: `[RSA-PSS-2048: READY]`, `[RSA-OAEP-2048: READY]`, `[ARGON2ID_SALT: ARMED]`.
   - Role selector styled as an industrial rotary switch: `[OPERATOR]`, `[AUDITOR]`, `[ADMIN]`.
   - Retain form names `username`, `email`, `password`, `confirm_password` and required test strings: `'MediaGuard Registration'`, `'Zero-Plaintext Security'`, `'2048-bit RSA-PSS'`.
3. `auth/setup_2fa.html`:
   - Style as the **Cryptographic Seed Enrollment Terminal**.
   - Invert QR code on a dark scanning plate with corner reticles.
   - Build 6-character monospace aperture for TOTP verification.
   - Retain required test strings: `'Activate Authenticator App'`, `'/auth/totp-qr'`, `'name="code"'`, `'Verify & Activate Account'`.

**Requirements for Task 6 (Vault & Ingestion):**
1. `media/upload.html`:
   - Style as the **Digital Evidence Ingestion Chamber**.
   - Ingestion aperture well with corner targeting brackets and vertical laser scanning line.
   - Real-time pipeline indicators: `[1. Magic Bytes] ➔ [2. SHA-256 Stream] ➔ [3. DCT pHash] ➔ [4. RSA-PSS Sign] ➔ [5. AES-256-GCM Envelope]`.
   - Preserve input ID `#media-file` and form field `name="media_file"`.
2. `media/library.html`:
   - Style as the **Encrypted Evidence Locker**.
   - Top telemetry rail: total assets, encrypted volume, ledger status.
   - Empty state transformed into **Cryptographic Vault Armed State** showing AES-256-GCM online, RSA-PSS verified, and zero-plaintext storage indicator.
   - Populated state: Dense tabular layout with filetype glyphs, grouped 12-char SHA-256 hex chips, pHash frequency badges, and tactile icon buttons (`[VIEW]`, `[DECRYPT]`, `[CERT]`, `[VERIFY]`).
   - Preserve table class `.table-vault`.
3. `media/preview.html`:
   - Style as the **Decrypted Evidence Inspection Console**.
   - Left Flank: Optical Evidence Lightbox with crosshair reticles, dimension telemetry, and warning watermark `IN-MEMORY DECRYPTED VIEW // CIPHERTEXT PRESERVED ON DISK`.
   - Right Flank: Cryptographic provenance plate with full SHA-256, pHash, RSA-PSS signature verification indicator, and PDF certificate export button.
   - Preserve image data URL format `'data:image/png;base64,'` tested by `test_media_routes.py`.

**Constraints:**
- STRICT ZERO INLINE STYLES (`style="..."`).
- Run tests: `python -m pytest tests/test_frontend.py tests/test_media_routes.py -v`.
- Commit changes.
- Write report to: `d:\Projects\Unii\IS Project\.superpowers\sdd\stream-b-report.md`.
