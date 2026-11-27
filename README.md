# Info Sec Project — MediaGuard

> **About this Project (Non-Technical Summary):**  
> **MediaGuard** is a media authenticity and verification system designed to protect digital photos and videos from being tampered with, edited, or faked. When you upload and register a file, the system creates a unique digital fingerprint and generates a tamper-proof verification certificate. Anyone can then submit a file to instantly check whether it is 100% original and untampered, or if it has been altered, modified, or re-saved.

> **CS-353 Information Security (2+1) — Semester Project (CLO-3)**  
> **National University of Sciences & Technology (NUST) · SEECS**  
> **Instructor:** Ms. Hirra Anwar  
> **Team Members:** Abdul Moiz (541687), Aarish Muhammad (542859), Hanya Zubair (550985)

---

## 1. Project Overview
**MediaGuard** is an institutional-grade, zero-trust digital media provenance and verification web application designed to protect images and videos against tampering, deepfakes, and unauthorized modification.

### Core Cryptographic Capabilities:
- **Custom Pure-Python Cryptographic Engines (`app/core/custom_crypto/`):**
  - **Custom SHA-256 (FIPS 180-4):** Pure-Python 64-round streaming compression engine powering file integrity checks and the audit ledger.
  - **Custom HMAC (RFC 2104) & TOTP (RFC 6238):** From-scratch keyed-hash MAC, Base32 decoder, and 6-digit TOTP authenticator verification.
  - **Custom 2D-DCT Perceptual Hashing (pHash):** Pure-Python separable 2D Discrete Cosine Transform and Hamming distance engine.
  - **Custom AES-256-CTR + HMAC-SHA256 (AEAD):** Pure-Python Rijndael block cipher (GF($2^8$) S-box, key expansion, MixColumns) in CTR mode with Encrypt-then-MAC authentication.
- **Standard Library Primitives (High-Complexity Boundaries):**
  - **Key Separation Principle:** Dual independent RSA-2048 key pairs per user (`cryptography` for 1024-bit prime generation, RSA-PSS signatures, and RSA-OAEP key wrapping).
  - **Password & Key Protection at Rest:** **Argon2id** (`argon2-cffi`) for login passwords and **scrypt** ($N=16384, r=8, p=1$) + **AES-256-GCM** for private key encryption under [`storage/key_storage/`](storage/key_storage/).
- **Dual-Check Public Verification:** Universal public portal (`/verify`) open to unauthenticated guests, verifying both byte-for-byte fidelity (**SHA-256**) and provenance authenticity (**RSA-PSS**), accompanied by perceptual diagnostics (**pHash** Hamming distance).
- **Digitally Signed PDF Certificates:** Generated dynamically with embedded **QR codes** linking straight to the public verification portal.
- **Tamper-Evident Audit Trail:** Blockchain-style hash-chained log (`audit_log`) with a 1-click cryptographic integrity verification tool for the Auditor role.
- **Live "Before & After" Demonstrator (`SECURE_MODE`):** An administrative switch allowing real-time viva demonstrations of vulnerabilities vs defenses across 8 OWASP Top 10 categories.

---

## 2. Quickstart & Installation

### Prerequisites:
- Python 3.11+
- Google Chrome or Chromium (for real-browser E2E testing)

### Installation:
```bash
# 1. Clone or navigate to the repository root
cd "d:/Projects/Unii/IS Project"

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Initialize the database
python -c "from app import create_app; from app.database.db import init_db; app = create_app(); init_db(app); print('Database initialized!')"

# 4. Start the application
python run.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000/`**

---

## 3. Automated Test Suite & Security Verification

MediaGuard is verified with 100% test pass rate across 105 automated tests and real-browser automation:

```bash
# Run all 105 unit and integration tests
python -m pytest tests/ -v

# Run dependency vulnerability audit (0 CVEs)
python -m pip_audit

# Run the real-browser Playwright E2E automation script
python experiments/browser_e2e_qa.py
```

---

## 4. Viva Voce & Classroom Demonstration Guide

Follow this 5-minute flow during evaluation with Ms. Hirra Anwar:

1. **User Registration & 2FA (`/auth/register`):**
   - Register a new user (`alice`).
   - Scan the TOTP QR code on `/auth/setup-2fa` using Google Authenticator or enter the 6-digit code.
   - Show that dual RSA key pairs were generated and saved as encrypted files in `storage/key_storage/`.
2. **Media Vault & Zero-Plaintext Storage (`/media/upload`):**
   - Upload an authentic photograph.
   - Show that the stored file in `storage/encrypted_media/*.enc` is unreadable ciphertext.
   - Click **"Download Certificate"** to open the generated PDF with embedded QR code.
3. **Public Verification (`/verify`):**
   - Open an incognito browser window (unauthenticated guest).
   - Enter the Certificate ID and upload the original file -> Displays **Green "AUTHENTIC"** card.
   - Upload a modified/cropped file against the same ID -> Displays **Red "MODIFIED"** card with pHash visual similarity analysis.
4. **Tamper-Evident Audit Trail (`/audit`):**
   - Log in as the `Auditor`.
   - Click **"Verify Entire Audit Chain"** -> Confirms all cryptographic hash linkages are intact.
5. **Live "Before and After" Demonstrations (`/admin/secure-mode`):**
   - Log in as `Admin`.
   - Toggle `SECURE_MODE` from True to False.
   - Show how an IDOR or SQLi attack succeeds in vulnerable mode.
   - Toggle back to True -> Show the exact same attack blocked with `403 Forbidden` and parameterized query defense.
6. **Attack Simulation Lab (`/experiments`):**
   - Trigger any of the 6 attack simulations (Pixel Tampering, File Replacement, Signature Forgery, Wrong Key, Unauthorized Decryption, Bit-Flipping) and watch the diagnostic console output the cryptographic mitigation.

---

## 5. Evidence Screenshots

Full-page screenshots captured during automated real-browser execution are available in [`docs/evidence/`](docs/evidence/):
- `01_landing_page.png`: Modern, high-contrast dark cybersecurity design system.
- `02_setup_2fa_qr.png`: TOTP 2FA pairing screen with QR code and manual fallback.
- `03_user_media_vault_empty.png`: User media vault dashboard.
- `04_media_upload_form.png`: Drag-and-drop media vault upload interface.
- `05_media_vault_with_asset.png`: Registered media asset with SHA-256 badge and certificate download link.
- `06_public_verify_authentic.png`: Public verification portal showing **AUTHENTIC** verdict.
- `07_public_verify_tampered.png`: Public verification portal showing **MODIFIED** verdict with pHash diagnostics.
- `08_audit_log_dashboard.png`: Tamper-evident hash-chained audit log viewer.
- `09_audit_chain_verified_banner.png`: 1-Click chain integrity check banner (**Intact**).
- `10_admin_secure_mode_owasp.png`: Admin Before/After demonstrator matrix covering 8 OWASP Top 10 categories.
- `11_attack_simulations_lab.png`: 6-card attack simulation suite.
- `12_simulation_result_console.png`: Live cryptographic telemetry console output.
- `Certificate_<id>.pdf`: High-resolution, verifiable PDF certificate with dynamic QR code.

---
*Developed for NUST SEECS CS-353 Information Security Semester Project.*
