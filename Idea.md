# MediaGuard – Secure Media Authenticity & Integrity Verification System
## Comprehensive Master Specification, System Architecture & Academic Blueprint

---

### Academic & Project Metadata
- **Institution:** National University of Sciences & Technology (NUST)
- **School:** School of Electrical Engineering and Computer Science (SEECS)
- **Faculty:** Faculty of Computing
- **Course:** CS-353 Information Security (2+1) — Semester Project (CLO-3)
- **Course Instructor:** Ms. Hirra Anwar
- **Start Date:** November 16, 2026
- **Project Title:** MediaGuard – Secure Media Authenticity & Integrity Verification System
- **Project Repository:** `d:/Projects/Unii/IS Project/`
- **Team Members & Core Responsibilities:**
  1. **Abdul Moiz (CMS ID: 541687):**
     - STRIDE Threat Analysis, CIA Triad & OWASP Top 10 Mapping.
     - Input and file upload validation (MIME/magic bytes, file size caps, secure filenames).
     - Parameterized SQL queries, rate limiting, and brute-force account lockout.
     - Security headers, custom safe error pages, and server-side defensive architecture.
     - Automated test suite (`pytest`), dependency vulnerability scanning (`pip-audit`), attack scripts, final report, and presentation slides.
  2. **Aarish Muhammad (CMS ID: 542859):**
     - Flask application core, request lifecycle, session hardening, and CSRF protection.
     - Role-Based Access Control (RBAC: User, Auditor, Admin) and endpoint authorization.
     - Per-user cryptographic key management (scrypt KDF, AES-256-GCM private key encryption).
     - Symmetric envelope encryption (AES-256-GCM per-file key generation, RSA-OAEP key wrapping).
     - Multi-Factor Authentication via TOTP (`pyotp`).
     - System-level `SECURE_MODE` toggle engine for live before-and-after vulnerability demonstrations.
  3. **Haniyya Zubair (CMS ID: 550985):**
     - Streamed SHA-256 cryptographic hashing and perceptual hashing (pHash via `imagehash`).
     - Deterministic canonical Registration Manifest generation and RSA-PSS digital signing/verification.
     - Public Verification Portal (unauthenticated guest verification).
     - Verification Certificate generation (digitally signed PDF with embedded dynamic QR code).
     - Cryptographically linked, tamper-evident hash-chained audit logging engine.

---

## 1. Project Overview & Problem Statement

### 1.1 The Real-World Problem
Digital images and videos are increasingly forged, re-encoded, deepfaked, or doctored for malicious purposes:
- **Legal & Judicial Evidence:** Disputed visual evidence in courtrooms where authenticity, provenance, and original timestamps determine case outcomes.
- **Journalism & Fact-Checking:** News agencies receiving user-submitted footage during conflicts or breaking news with no verifiable chain of custody.
- **Insurance Claims:** Fraudulent or manipulated photos of vehicle or property damage submitted for claim payouts.
- **Academic & Medical Records:** Altered scientific data, scanned credentials, or medical radiology imagery.

In all these scenarios, stakeholders face common dilemmas:
1. *Was this media modified or altered after it was initially recorded or submitted?*
2. *Who asserts provenance over this file, and did they digitally sign it with a trusted key?*
3. *When was the media registered with the system?*
4. *Can third parties verify its integrity without being given access to read or decrypt the owner's private files?*

### 1.2 The MediaGuard Solution
**MediaGuard** is a robust, modular, Python-based Information Security system designed to safeguard digital media against unauthorized modification, tampering, identity spoofing, and unauthorized access. 

MediaGuard couples **high-speed authenticated symmetric encryption** with **public-key cryptography, cryptographic hashing, perceptual similarity diagnostics, and tamper-evident logging**:
- **Zero-Plaintext Storage:** Original media files are never retained in unencrypted plaintext on the server.
- **Envelope Encryption (Hybrid Cryptography):** Each media file is encrypted with a fresh, random AES-256-GCM key. That symmetric key is wrapped using the owner's RSA-OAEP public key.
- **Cryptographic Provenance:** A canonical, tamper-proof JSON **Registration Manifest** is generated for every media file, binding the media's exact SHA-256 hash, perceptual pHash, filename, size, owner identity, and server timestamp. This manifest is digitally signed using the owner's **RSA-PSS private signing key**.
- **Public Verification & Verifiable Certificates:** Anyone (including unauthenticated guests, journalists, or legal auditors) can verify a file against its registered record using the public portal or by scanning the QR code on an issued **PDF Verification Certificate**.
- **Live Educational Demonstrator (`SECURE_MODE`):** Includes a runtime toggle switch (`SECURE_MODE = True/False`) that enables live before-and-after demonstrations of OWASP Top 10 vulnerabilities and security attacks for academic evaluations.

### 1.3 Scope, Boundaries & Cryptographic Limitations
1. **Byte-Level Integrity vs. Physical Truth:** MediaGuard cryptographically proves byte-for-byte fidelity and perceptual consistency relative to the registered original. It does *not* claim to detect whether an image was staged, manipulated, or synthesized prior to its initial registration.
2. **Identity Association:** A digital signature proves mathematically that the owner's private signing key was used. It establishes accountability assuming the user account and private keys were securely provisioned and kept secret.
3. **Encoding & Transcoding Sensitivities:** Because SHA-256 operates on raw binary byte streams, any re-encoding, metadata stripping, or format conversion alters the hash completely. MediaGuard bridges this gap by coupling **SHA-256** (strict byte-for-byte integrity) with **pHash** (perceptual similarity diagnostics) to explain whether a failure was due to benign compression or malicious visual tampering.

---

## 2. Core Objectives & Course Alignment (NUST SEECS)

The project directly fulfills all requirements of the **CS-353 Information Security Semester Project (CLO-3)** rubric:
1. **Real-World Problem:** Securing evidentiary digital media against forgery, tampering, and repudiation.
2. **Working Solution:** A functional Flask web application handling end-to-end registration, verification, retrieval, and audit logging.
3. **CIA Triad Coverage:** Implements concrete defenses across all three pillars: **Confidentiality**, **Integrity**, and **Availability**.
4. **OWASP Top 10 Defenses:** Defends against and demonstrates 8 distinct OWASP Top 10 vulnerability categories.
5. **Beyond Password Hashing:** Implements dual RSA key pairs, AES-GCM envelope encryption, TOTP Multi-Factor Authentication, Role-Based Access Control, and hash-chained audit trails.
6. **"Before and After" Live Demonstration:** Integrates an administrative `SECURE_MODE` switch to display vulnerable execution paths followed by active defenses.

---

## 3. Technology Stack & Library Justification

| Layer / Component | Technology | Version / Specification | Rationale & Security Justification |
| :--- | :--- | :--- | :--- |
| **Language** | Python | 3.11+ | Modern, secure typing, robust cryptographic ecosystem, clean modular architecture. |
| **Web Framework** | Flask + Jinja2 | Latest Stable | Server-side templating enables strict Content Security Policy (CSP), custom session cookie flags (`HttpOnly`, `SameSite=Strict`), CSRF protection, and precise route-level authorization (unlike Streamlit). |
| **Database** | SQLite 3 | Embedded | Portable, lightweight, reliable ACID transactions; accessed strictly through parameterized queries to eliminate SQL Injection. |
| **Symmetric Cipher** | AES-256-GCM | `cryptography` hazmat | Authenticated Encryption with Associated Data (AEAD); guarantees both confidentiality and ciphertext integrity via a 128-bit authentication tag. |
| **Asymmetric Cipher** | RSA (2048/3072 bit) | `cryptography` hazmat | Asymmetric key operations. Follows **Key Separation Principle** with dual key pairs: RSA-PSS for signatures and RSA-OAEP for key wrapping. |
| **File Hashing** | SHA-256 | `hashlib` (streamed) | NIST standard cryptographic hash producing 256-bit collision-resistant digests. Streamed in 64KB chunks to prevent RAM exhaustion on large video uploads. |
| **Perceptual Hashing** | pHash (DCT-based) | `imagehash` + `Pillow` | Computes a 64-bit perceptual fingerprint based on Discrete Cosine Transform. Allows diagnosing visual similarity (Hamming distance) when hashes differ. |
| **Password Hashing** | Argon2id | `argon2-cffi` | Winner of the Password Hashing Competition; state-of-the-art memory-hard algorithm resistant to GPU/ASIC brute-forcing and side-channel attacks. |
| **Key Derivation** | scrypt KDF | `cryptography` hazmat | Memory-hard Key Derivation Function ($N=2^{14}, r=8, p=1$) used to derive Key Encryption Keys ($KEK$) from user passwords to protect private RSA keys. |
| **Multi-Factor Auth** | TOTP (RFC 6238) | `pyotp` + `qrcode` | Time-based One-Time Password providing out-of-band two-factor authentication, satisfying OWASP A07 defenses. |
| **Certificate Engine** | PDF Generation | `reportlab` + `qrcode` | Produces cryptographically verifiable PDF Verification Certificates containing metadata, hashes, signatures, and scannable verification QR codes. |
| **Testing & Auditing** | `pytest` + `pip-audit` | Latest Stable | Automated test coverage for cryptographic routines; continuous dependency scanning against CVE databases. |

---

## 4. Cryptographic Architecture & Design Specifications

```
                                [ User Master Password ]
                                            |
                                  scrypt KDF (with Salt)
                                            |
                                            v
                                 [ 256-bit AES-GCM KEK ]
                                            |
                       +--------------------+--------------------+
                       |                                         |
                       v                                         v
       [ Encrypt Private Signing Key ]          [ Encrypt Private Encryption Key ]
                       |                                         |
                       v                                         v
         storage/key_storage/<uid>/                storage/key_storage/<uid>/
              signing_key.enc                           encryption_key.enc
```

### 4.1 Key Separation Principle (Dual RSA Key Pairs)
A common vulnerability in amateur cryptographic implementations is key reuse (e.g., using the same RSA private key to sign documents and decrypt data). This exposes the system to cross-protocol attacks where an attacker tricks a user into signing a chosen ciphertext.

MediaGuard enforces strict **separation of duties** by provisioning **two separate RSA key pairs** per user upon account creation:
1. **Digital Signing Key Pair:**
   - **Private Signing Key ($K_{sign\_priv}$):** Used strictly with **RSA-PSS** (Probabilistic Signature Scheme, SHA-256, MGF1) to sign canonical registration manifests.
   - **Public Verification Key ($K_{sign\_pub}$):** Stored in the SQLite database and exported on certificates; used universally to verify signatures.
2. **Encryption Key Wrapping Key Pair:**
   - **Public Encryption Key ($K_{enc\_pub}$):** Stored in the SQLite database; used during media upload to wrap (encrypt) the random per-file AES key via **RSA-OAEP**.
   - **Private Encryption Key ($K_{enc\_priv}$):** Kept strictly encrypted; used exclusively during media retrieval by the authenticated owner to unwrap the AES key.

### 4.2 Private Key Protection at Rest
- Private key PEMs are **never saved in plaintext** in the database or on the filesystem.
- When a user registers:
  1. A random 16-byte salt is generated.
  2. The user's password derives a 256-bit Key Encryption Key ($KEK$) using **scrypt** ($N=2^{14}, r=8, p=1$).
  3. Both private keys are encrypted with $KEK$ using **AES-256-GCM** (producing ciphertexts, random 96-bit nonces, and 128-bit authentication tags).
  4. Encrypted blobs are saved to `storage/key_storage/<user_id>/signing_key.enc` and `storage/key_storage/<user_id>/encryption_key.enc`.
  5. The database holds only file paths, salt, nonces, and tags.
- Decrypted private keys exist **only in memory during an active, authenticated session** and are wiped upon logout or session expiry.

### 4.3 Symmetric Envelope Encryption (AES-256-GCM)
- For every registered file:
  1. Generate a cryptographically secure random 256-bit symmetric key ($K_{AES} \leftarrow \text{os.urandom}(32)$).
  2. Generate a fresh, unique 96-bit nonce ($N_{AES} \leftarrow \text{os.urandom}(12)$). **Nonces are never reused under the same key.**
  3. Encrypt the file using **AES-256-GCM**, yielding ciphertext $C_{media}$ and a 128-bit authentication tag $T_{AES}$.
  4. Wrap $K_{AES}$ using the owner's RSA public encryption key ($K_{enc\_pub}$) with **RSA-OAEP** (SHA-256, MGF1):
     $$C_{AES} = \text{RSA-OAEP-Encrypt}(K_{enc\_pub}, K_{AES})$$
  5. Save $C_{media}$ to `storage/encrypted_media/<media_id>.enc`.
  6. Store $C_{AES}$, $N_{AES}$, and $T_{AES}$ in the SQLite `media` table.
- **Zero-Plaintext Policy:** The plaintext upload is immediately and permanently removed from disk.

### 4.4 Deterministic Canonical Manifest & RSA-PSS Signatures
To guarantee that metadata (filename, owner, timestamp, size) cannot be detached, altered, or replayed with a different file, signatures are computed over a **canonical JSON Registration Manifest**:

```json
{
  "media_id": "urn:uuid:6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "owner_id": 1,
  "owner_username": "aarish_muhammad",
  "original_filename": "crime_scene_photo.jpg",
  "file_size": 4194304,
  "mime_type": "image/jpeg",
  "sha256_hash": "a81f9c2d7e8b61c5a9809b4e2f9d8a3c5b2e19d7f6a4c2e1b8a9c7d5e3f1b4a2",
  "phash": "d3839c4f2e6a1b05",
  "registration_timestamp_utc": "2026-11-21T10:30:00Z",
  "cipher_suite": "AES-256-GCM / RSA-OAEP-SHA256 / RSA-PSS-SHA256"
}
```

- Canonicalization: Keys sorted alphabetically, compact JSON formatting (no superfluous whitespace), UTF-8 encoded.
- The canonical string is hashed with SHA-256 and signed with $K_{sign\_priv}$ using **RSA-PSS**:
  $$\sigma = \text{RSA-PSS-Sign}(K_{sign\_priv}, \text{SHA-256}(\text{CanonicalManifest}))$$
- Verifying the signature requires only $K_{sign\_pub}$, the manifest, and $\sigma$.

---

## 5. End-to-End System Workflows

```
========================================================================================
                              WORKFLOW A: REGISTRATION & SETUP
========================================================================================
[ User Inputs Credentials ]
            |
            +---> Argon2id Hash Password -> Store in DB
            +---> Generate Secret -> Display TOTP QR Code
            +---> Generate Dual RSA Key Pairs (Signing & Wrapping)
            +---> scrypt KDF(Password, Salt) -> Derives KEK
            +---> AES-256-GCM Encrypt Private Keys -> Store in storage/key_storage/
            +---> Store Public Keys & Metadata in SQLite

========================================================================================
                              WORKFLOW B: MEDIA REGISTRATION
========================================================================================
[ Upload File: JPG/PNG/MP4/MOV ]
            |
            +---> Validate Magic Bytes (MIME) & Enforce Size Cap
            +---> Stream File -> Compute SHA-256 & pHash
            +---> Construct Canonical JSON Manifest
            +---> Sign Manifest with RSA-PSS using Owner's Private Signing Key
            +---> Generate Random AES-256 Key + 96-bit Nonce
            +---> AES-256-GCM Encrypt File -> Save to storage/encrypted_media/*.enc
            +---> Wrap AES Key with Owner's Public Encryption Key (RSA-OAEP)
            +---> Store Metadata, Nonce, Tag, Wrapped Key, Manifest & Signature in DB
            +---> Generate Verification Certificate (PDF with QR Code)
            +---> Append Record to Hash-Chained Audit Log
            +---> Wipe Unencrypted Plaintext File

========================================================================================
                              WORKFLOW C: PUBLIC VERIFICATION
========================================================================================
[ Verifier Uploads Suspect File + Inputs Certificate/Media ID (or scans QR) ]
            |
            +---> Recalculate Streamed SHA-256 & pHash
            +---> Retrieve Registered Manifest & Public Signing Key from DB
            |
            +---> CHECK 1 (Byte Integrity): Recalculated SHA-256 == Manifest SHA-256?
            +---> CHECK 2 (Authenticity):   Verify RSA-PSS Signature on Manifest?
            +---> DIAGNOSTIC (pHash):       Hamming Distance Comparison
            |
            v
[ Synthesize Granular Verdict: AUTHENTIC / MODIFIED / INVALID SIGNATURE / UNKNOWN ]
            |
            +---> Append Verification Attempt to Verification History & Audit Log

========================================================================================
                              WORKFLOW D: SECURE RETRIEVAL
========================================================================================
[ Authenticated Owner Requests Media Retrieval ]
            |
            +---> Verify Owner Identity & Active Session Credentials
            +---> Decrypt Owner's Private Encryption Key via In-Memory KEK
            +---> Unwrap AES-256 Key via RSA-OAEP Private Key
            +---> AES-256-GCM Decrypt Ciphertext from storage/encrypted_media/
            +---> Verify Authentication Tag (Halt immediately if corrupted)
            +---> Recalculate Plaintext SHA-256 -> Match with Manifest
            +---> Stream Decrypted File to Browser for Preview / Download
```

### 5.1 Verification Outcomes Detailed

| Verdict | SHA-256 Check | RSA-PSS Signature | pHash Diagnostic | Interpretation & Clinical Meaning |
| :--- | :---: | :---: | :---: | :--- |
| **AUTHENTIC** | Match | Valid | Distance = 0 | **Verified Original:** File content is identical byte-for-byte to the registered original. Record signature is mathematically valid. |
| **MODIFIED (Perceptual Match)** | Mismatch | Valid | Distance $\le 5$ | **Format/Compression Change:** Bytes differ, but visual content is perceptually identical (e.g., image re-saved as JPEG with different compression quality). |
| **MODIFIED (Visual Tamper)** | Mismatch | Valid | Distance $> 5$ | **Content Modified / Replaced:** Image/video pixels or frames have been altered, cropped, doctored, or replaced with a different file. Manifest record remains authentic. |
| **INVALID SIGNATURE** | Any | Invalid | Any | **Compromised Record / Forgery:** The registration manifest has been altered or forged, or the digital signature cannot be verified with the registered public key. |
| **UNKNOWN** | N/A | N/A | N/A | **Unregistered Media:** The supplied Certificate ID / Media ID does not exist in the database. |

---

## 6. Security Analysis & Course Requirement Mappings

### 6.1 Mapping to the CIA Triad
- **Confidentiality:**
  - Encrypted media storage at rest using AES-256-GCM.
  - Per-file symmetric keys protected via RSA-OAEP key wrapping.
  - User private keys protected at rest using scrypt-derived KEK and AES-256-GCM.
  - Sensitive files accessible only to authorized owners via role-based access control (RBAC).
- **Integrity:**
  - SHA-256 cryptographic hashing validates byte-level file integrity.
  - RSA-PSS digital signatures protect manifest metadata against tampering and guarantee non-repudiation.
  - AES-GCM 128-bit authentication tags prevent bit-flipping attacks on ciphertext.
  - Hash-chained audit logs ensure that historical logs cannot be secretly altered or deleted.
- **Availability:**
  - Strict upload file size limits (50MB cap) and magic-byte validation prevent disk and memory exhaustion.
  - Streamed chunk-based hashing (64KB blocks) prevents memory denial-of-service on large files.
  - IP and account rate limiting blocks automated denial-of-service attacks.
  - Account lockout after 5 consecutive failed login attempts mitigates brute-force attacks.

### 6.2 The `SECURE_MODE` Demonstration Switch (OWASP Top 10)
MediaGuard provides a dedicated runtime switch (`SECURE_MODE = True/False`) to demonstrate the "before and after" requirement stipulated by Ms. Hirra Anwar:

```
+----------------------------------------------------------------------------------------------------+
|                                    SECURE_MODE ARCHITECTURE                                        |
|                                                                                                    |
|   [ Incoming Request ] ---> [ SECURE_MODE == True ? ]                                              |
|                                     |                                                              |
|                  +------------------+------------------+                                           |
|                  |                                     |                                           |
|                  v (TRUE: Protected)                   v (FALSE: Vulnerable Mode for Viva)         |
|       - Parameterized SQLite Queries        - Raw String Concatenation (SQLi Exposed)              |
|       - Strict Session & Ownership Checks   - IDOR: Direct File ID Access Allowed                  |
|       - AES-256-GCM Envelope Encryption     - Plaintext / Unauthenticated File Storage             |
|       - Account Lockout & TOTP Enforced     - Unlimited Brute Force & Single Factor                |
|       - Generic Safe Error Handlers         - Verbose Tracebacks & Internal Path Leaks             |
|       - Hash-Chained Audit Trail Active     - Plain Mutable Log Rows (Tampering Undetected)        |
+----------------------------------------------------------------------------------------------------+
```

#### Detailed OWASP Top 10 Mapping Matrix

| OWASP Vulnerability | Vulnerability Before (`SECURE_MODE = False`) | Defense After (`SECURE_MODE = True`) | CIA Goal |
| :--- | :--- | :--- | :--- |
| **A01:2021 – Broken Access Control** | **IDOR & Privilege Escalation:** User B can download User A's private media by changing `media_id` in the URL; standard users can hit `/admin` routes. | **Server-side Ownership & RBAC:** Enforces `session['user_id'] == media.owner_id` and strict role decorators (`@require_role('Admin')`); returns 403 Forbidden. | Confidentiality |
| **A02:2021 – Cryptographic Failures** | **Plaintext & Unauthenticated Storage:** Media saved unencrypted on disk; private keys in plaintext; or using ECB mode without integrity tags. | **Hybrid Envelope Encryption:** AES-256-GCM per file, RSA-OAEP key wrapping, scrypt memory-hard KDF, zero plaintext retention. | Confidentiality & Integrity |
| **A03:2021 – Injection** | **SQL Injection & Path Traversal:** Database queried via string formatting (`f"SELECT * FROM media WHERE id='{media_id}'"`); uploads keep raw filenames (`../../etc/evil.sh`). | **Parameterized Queries & Sanitization:** All queries use `cursor.execute("...", (params,))`; filenames sanitized with `secure_filename()` and stored with UUIDs. | Integrity & Availability |
| **A04:2021 – Insecure Design** | **Unrestricted Upload Abuse:** No file size caps or type validation; allows server disk exhaustion and malicious executable uploads. | **Defensive Architecture:** Enforced 50MB size limit, MIME validation via magic bytes (`python-magic`/header sniffing), streamed chunking. | Availability |
| **A05:2021 – Security Misconfiguration** | **Information Leaks:** Flask debug mode enabled; uncaught exceptions display complete stack traces, environment variables, and filesystem paths. | **Hardened Production Profile:** Custom error handlers (404, 500); hardened HTTP security headers (`Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`). | Confidentiality |
| **A06:2021 – Vulnerable Components** | **Outdated Dependencies:** Dependencies with known Common Vulnerabilities and Exposures (CVEs) present in environment. | **Automated Auditing:** Automated `pip-audit` scan integrated into test suite; verified zero CVEs across all installed libraries. | Integrity |
| **A07:2021 – Identification & Auth Failures** | **Brute-Force & Credential Stuffing:** Unlimited password attempts allowed; single-factor authentication only. | **Account Lockout & MFA:** Account locked for 15 minutes after 5 failed attempts; mandatory TOTP 2FA (`pyotp`) for all logins. | Confidentiality |
| **A08:2021 – Software & Data Integrity Failures** | **Silent Tampering:** Modified media files accepted as valid; tampered registration manifests accepted without signature check. | **Cryptographic Verification:** SHA-256 hash comparison detects byte-level changes; RSA-PSS verifies manifest signature authenticity. | Integrity |
| **A09:2021 – Security Logging Failures** | **Log Tampering & Inadequate Audit:** Logs stored in plain mutable text; rogue admin can delete verification records without trace. | **Hash-Chained Audit Trail:** Blockchain-style `prev_hash` linkage; any row deletion or modification immediately breaks the chain. | Integrity & Accountability |

### 6.3 STRIDE Threat Modeling Table
To satisfy the 1-2 page STRIDE threat analysis deliverable:

| Letter | Threat Category | Threat Scenario in MediaGuard | Potential Impact | MediaGuard Countermeasure | OWASP Item |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **S** | **Spoofing** | Attacker impersonates an authorized photographer to register falsified media. | Fraudulent provenance record created under victim's name. | Argon2id password hashing + mandatory TOTP 2FA + per-user RSA private signing key. | A07 |
| **T** | **Tampering** | Attacker alters pixels in a registered image or modifies database rows. | Court or journalist accepts altered media as genuine original. | SHA-256 byte comparison + RSA-PSS digital signatures + AES-GCM authentication tag. | A08 |
| **R** | **Repudiation** | Media owner registers a controversial photo and later falsely denies ownership. | Accountability failure; loss of legal evidentiary standing. | Non-repudiable RSA-PSS signature over canonical manifest + hash-chained audit log. | A09 |
| **I** | **Information Disclosure** | Unauthorized user or filesystem intruder reads stored sensitive media. | Confidential photos or videos leaked publicly. | AES-256-GCM encryption at rest; wrapped AES keys via RSA-OAEP; scrypt-encrypted private keys. | A02 |
| **D** | **Denial of Service** | Malicious client floods the server with multi-gigabyte uploads or spams login. | Server disk fills up, CPU exhausts, legitimate users locked out. | Streamed hashing, strict 50MB file size cap, IP/account rate limiting, 5-attempt lockout. | A04 |
| **E** | **Elevation of Privilege** | Standard User modifies session or request parameters to execute Admin functions. | Unauthorized access to user management, lockouts, or audit logs. | Server-side Role-Based Access Control (RBAC) with `@require_role()` decorators on all routes. | A01 |

---

## 7. Security Attack Simulations & Viva Demonstrations

MediaGuard includes a dedicated **Attack Simulation Engine** (`experiments/attack_simulations.py` and a UI dashboard) to demonstrate 6 controlled security experiments during project evaluation:

### Simulation 1: Image Byte & Pixel Modification Attack
- **Objective:** Demonstrate that minor visual changes completely break SHA-256 integrity while pHash reveals visual similarity.
- **Procedure:**
  1. Register `original.jpg`. Note registered SHA-256 (`e3b0c44...`) and pHash (`d3839c...`).
  2. The simulation alters a single pixel's RGB value or crops 1% of the border, saving as `tampered.jpg`.
  3. Submit `tampered.jpg` to the verification portal.
- **Expected Outcome:** Verification reports **MODIFIED**. SHA-256 mismatch detected immediately. pHash diagnostic indicates Hamming distance $\le 5$ (visual match, byte mismatch).

### Simulation 2: File Replacement Attack
- **Objective:** Demonstrate detection when a completely different file is substituted under an existing Certificate ID.
- **Procedure:**
  1. Take registered `contract.pdf` / `photo.jpg`.
  2. Upload an unrelated image `fake.png` under the registered Certificate ID.
- **Expected Outcome:** Verification reports **MODIFIED**. SHA-256 fails completely, and pHash Hamming distance $> 20$ confirms a completely different visual object.

### Simulation 3: Digital Signature & Manifest Tampering
- **Objective:** Demonstrate that modifying manifest metadata (e.g., changing timestamp or owner ID) invalidates the signature.
- **Procedure:**
  1. Retrieve registered canonical manifest from the database.
  2. Alter `"timestamp_utc"` or `"file_size"`.
  3. Execute signature verification against the altered manifest.
- **Expected Outcome:** Verification reports **INVALID SIGNATURE**. RSA-PSS verification returns `False`. The system rejects the record as compromised.

### Simulation 4: Wrong-Key Verification Attack
- **Objective:** Demonstrate that a digital signature cannot be verified with an arbitrary or forged public key.
- **Procedure:**
  1. Attempt to verify a valid manifest signature using Public Key B instead of the true Owner's Public Key A.
- **Expected Outcome:** RSA-PSS verification fails with `InvalidSignature`. Proves non-transferability of provenance.

### Simulation 5: Unauthorized Decryption & Key Wrapping Attack
- **Objective:** Demonstrate that possessing the ciphertext and database row is insufficient to decrypt media without the owner's private key.
- **Procedure:**
  1. Attacker obtains `storage/encrypted_media/<media_id>.enc` and `wrapped_aes_key`.
  2. Attacker attempts to unwrap the AES key using their own private key or an arbitrary key.
- **Expected Outcome:** RSA-OAEP decryption fails with `ValueError: Decryption failed`. Media cannot be decrypted.

### Simulation 6: Encrypted File Tampering (Ciphertext Bit-Flipping Attack)
- **Objective:** Demonstrate that authenticated encryption (AES-256-GCM) detects ciphertext tampering at the block level.
- **Procedure:**
  1. Flip a single bit in the stored `.enc` file or modify the 16-byte authentication tag.
  2. Authenticated owner attempts retrieval.
- **Expected Outcome:** AES-256-GCM decryption throws `InvalidTag`. The system terminates decryption immediately, refusing to release corrupted plaintext.

---

## 8. Theoretical & Extended Information Security Concepts

### 8.1 DES vs. AES Conceptual Evolution
In viva and reports, MediaGuard provides a comparative analysis highlighting why modern systems mandate AES over legacy DES/3DES:

| Feature | Data Encryption Standard (DES) | Advanced Encryption Standard (AES) |
| :--- | :--- | :--- |
| **Design Date** | 1977 (IBM / NIST) | 2001 (Rijndael, Vincent Rijmen & Joan Daemen) |
| **Structure** | 16-round Feistel network | Substitution-Permutation Network (SPN) |
| **Key Length** | 56 bits (effective) | 128, 192, or 256 bits (MediaGuard uses 256-bit) |
| **Block Size** | 64 bits (vulnerable to birthday attacks) | 128 bits |
| **Cryptanalysis Status** | **Broken:** Practical brute-force recovery in hours via EFF Deep Crack (1998) or modern GPUs. | **Secure:** No known practical attacks; exhaustive key search requires $2^{256}$ operations (astronomical). |
| **Mode in MediaGuard** | Deprecated / Unused | **AES-256-GCM:** Provides AEAD (Confidentiality + Authenticity). |

### 8.2 Classical Cryptography Demonstration (Caesar & Substitution Ciphers)
To illustrate the historical evolution from security through obscurity to modern Kerckhoffs' principle, MediaGuard includes a lightweight educational module demonstrating:
- **Caesar Cipher:** Shift cipher ($C \equiv P + k \pmod{26}$). Easily broken via frequency analysis or testing 25 possible keys.
- **Contrast with Modern Crypto:** Modern cryptography assumes the attacker knows the complete algorithm (AES/RSA) and source code; security relies exclusively on the secrecy and entropy of the key.

### 8.3 IoT Security Applications & Edge Deployment
MediaGuard's cryptographic architecture directly translates to securing Internet of Things (IoT) devices:
- **Surveillance & Dashcams:** Smart cameras and police bodycams compute streamed SHA-256 and sign manifests on-device with an onboard secure element (TPM / hardware enclave), offloading encrypted media to untrusted cloud storage.
- **Constrained Bandwidth:** Hashing and signing produce lightweight metadata (32-byte hash, 256-byte signature), enabling provenance checks over low-bandwidth cellular/mesh IoT networks without uploading full videos.
- **Tamper Evidence:** If physical camera memory cards are intercepted, AES-GCM prevents viewing, and signature checks prevent footage substitution.

### 8.4 GDPR & Privacy Compliance Principles
- **Data Minimization (Article 5(1)(c)):** MediaGuard discards unencrypted files immediately after encryption. Only essential metadata required for verification is retained.
- **Storage Limitation & Right to Erasure / "Crypto-Shredding" (Article 17):** If a user deletes media, MediaGuard permanently destroys the wrapped AES key and ciphertext. Without the 256-bit AES key, the data is mathematically unrecoverable.
- **Integrity & Confidentiality (Article 5(1)(f)):** End-to-end encryption at rest, secure key storage, and access controls guarantee compliance with GDPR security requirements.

---

## 9. Role-Based Access Control (RBAC) Specification

| Capability / Route | Unauthenticated Guest | User | Auditor | Admin |
| :--- | :---: | :---: | :---: | :---: |
| View Landing Page & About | Yes | Yes | Yes | Yes |
| Public Verification Portal (`/verify`) | Yes | Yes | Yes | Yes |
| Register Account & Setup MFA | Yes | No | No | No |
| Login / Logout / Session Mgmt | Yes | Yes | Yes | Yes |
| Upload & Register Media (`/media/upload`) | No | Yes | No | No |
| View Personal Media Library (`/media`) | No | Yes | No | No |
| Download Personal Decrypted Media (`/media/<id>/download`) | No | Yes (Own files) | No | No |
| Download Verification Certificate PDF | Yes (If has ID) | Yes | Yes | Yes |
| View Tamper-Evident Audit Logs (`/audit`) | No | No | Yes (Read-only) | Yes |
| Run Audit Chain Verification Tool | No | No | Yes | Yes |
| User Management & Account Unlocking (`/admin/users`) | No | No | No | Yes |
| Toggle `SECURE_MODE` Switch (`/admin/secure-mode`) | No | No | No | Yes |
| Run Security Attack Simulations (`/experiments`) | No | Yes | Yes | Yes |

---

## 10. Database Schema (SQLite)

```sql
-- Users Table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,             -- Argon2id string
    totp_secret TEXT NOT NULL,               -- Encrypted TOTP secret
    role TEXT NOT NULL DEFAULT 'User',       -- 'User', 'Auditor', 'Admin'
    public_signing_key TEXT NOT NULL,        -- PEM format
    public_encryption_key TEXT NOT NULL,     -- PEM format
    encrypted_signing_key_path TEXT NOT NULL,-- storage/key_storage/<uid>/signing_key.enc
    encrypted_encryption_key_path TEXT NOT NULL, -- storage/key_storage/<uid>/encryption_key.enc
    kdf_salt BLOB NOT NULL,                  -- 16-byte random salt for scrypt
    is_locked BOOLEAN DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Media Table
CREATE TABLE media (
    media_id TEXT PRIMARY KEY,               -- UUID string
    owner_id INTEGER NOT NULL,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,                 -- image/jpeg, image/png, video/mp4, video/quicktime
    file_size INTEGER NOT NULL,              -- Bytes
    sha256_hash TEXT NOT NULL,               -- 64-character hex string
    phash TEXT NOT NULL,                     -- 16-character hex string
    encrypted_file_path TEXT NOT NULL,       -- storage/encrypted_media/<uuid>.enc
    wrapped_aes_key BLOB NOT NULL,           -- RSA-OAEP encrypted AES key (256/384 bytes)
    nonce BLOB NOT NULL,                     -- 12-byte AES-GCM nonce
    auth_tag BLOB NOT NULL,                  -- 16-byte AES-GCM authentication tag
    registration_manifest TEXT NOT NULL,     -- Canonical JSON string
    digital_signature BLOB NOT NULL,         -- RSA-PSS signature bytes
    registration_timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Verification History Table
CREATE TABLE verification_history (
    verification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id TEXT,
    verifier_user_id INTEGER NULLABLE,       -- NULL for public guest verifications
    uploaded_filename TEXT NOT NULL,
    submitted_sha256 TEXT NOT NULL,
    submitted_phash TEXT NOT NULL,
    hash_match BOOLEAN NOT NULL,
    signature_valid BOOLEAN NOT NULL,
    phash_distance INTEGER NOT NULL,
    overall_status TEXT NOT NULL,            -- 'AUTHENTIC', 'MODIFIED', 'INVALID_SIGNATURE', 'UNKNOWN'
    verification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_id) REFERENCES media(media_id) ON DELETE SET NULL,
    FOREIGN KEY (verifier_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Hash-Chained Tamper-Evident Audit Log Table
CREATE TABLE audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NULLABLE,
    action TEXT NOT NULL,                    -- 'REGISTER_MEDIA', 'VERIFY_ATTEMPT', 'LOGIN_FAILURE', etc.
    details TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    prev_hash TEXT NOT NULL,                 -- SHA-256 hex string of previous row
    current_hash TEXT NOT NULL               -- SHA-256(log_id || timestamp || user_id || action || details || ip_address || prev_hash)
);
```

---

## 11. Directory & File Organization

```
d:/Projects/Unii/IS Project/
├── Idea.md                          # Master Blueprint & Comprehensive Specification
├── README.md                        # Quickstart Guide, Installation, and Viva Manual
├── requirements.txt                 # Pinned Python Dependencies
├── run.py                           # App Entry Point (python run.py)
├── config.py                        # Centralized Configuration & SECURE_MODE State
│
├── app/
│   ├── __init__.py                  # Flask App Factory, Middleware, Security Headers
│   │
│   ├── routes/                      # Route Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py                  # Login, Register, TOTP 2FA, Logout, Lockout
│   │   ├── media.py                 # Media Upload, Library, Secure Retrieval & Decryption
│   │   ├── verify.py                # Public & Authenticated Verification Portal
│   │   ├── audit.py                 # Tamper-Evident Audit Log & Chain Verifier (Auditor)
│   │   ├── admin.py                 # User Management & SECURE_MODE Controller (Admin)
│   │   └── experiments.py           # Attack Simulation Dashboard (Tampering, Bitflip, IDOR)
│   │
│   ├── core/                        # Modular Cryptographic & Security Engines
│   │   ├── __init__.py
│   │   ├── hashing.py               # Streamed SHA-256, pHash (imagehash)
│   │   ├── ciphers.py               # AES-256-GCM Encrypt/Decrypt, Tag Validation
│   │   ├── signatures.py            # Canonical Manifest Builder, RSA-PSS Sign/Verify
│   │   ├── key_management.py        # Dual Key Pair Gen, scrypt KDF, RSA-OAEP Wrapping
│   │   ├── certificate.py           # ReportLab PDF Certificate Generator with QR
│   │   ├── audit_chain.py           # Cryptographic Hash Chaining Engine
│   │   └── validators.py            # Magic Bytes (MIME), File Size & Path Sanitizer
│   │
│   ├── database/                    # Database Layer
│   │   ├── __init__.py
│   │   ├── db.py                    # SQLite Connection Context & Parameterized Helper
│   │   └── schema.sql               # SQLite Table DDL & Initial Admin Seed
│   │
│   ├── templates/                   # Clean, Modern Jinja2 Templates
│   │   ├── base.html                # Master Layout with CSRF & CSP Headers
│   │   ├── auth/
│   │   │   ├── login.html           # Login with Lockout Counter
│   │   │   ├── register.html        # Registration & Password Requirements
│   │   │   └── setup_2fa.html       # TOTP QR Code Scanner Page
│   │   ├── media/
│   │   │   ├── upload.html          # Drag-and-drop Media Upload Form
│   │   │   ├── library.html         # User Media Library
│   │   │   └── preview.html         # Authenticated In-Memory Decryption Viewer
│   │   ├── verify/
│   │   │   ├── verify.html          # Public Verification Portal (Drag & Drop)
│   │   │   └── result.html          # Granular Color-Coded Verdict Dashboard
│   │   ├── audit/
│   │   │   └── audit_log.html       # Audit Log Viewer & Chain Verifier Button
│   │   ├── admin/
│   │   │   ├── dashboard.html       # User Management & SECURE_MODE Controls
│   │   │   └── secure_mode.html     # Live Before-and-After Switch Demonstrator
│   │   └── experiments/
│   │       └── simulations.html     # Interactive Security Attacks & Results
│   │
│   └── static/
│       ├── css/
│       │   └── style.css            # Professional, Clean Interface Styling
│       └── js/
│           └── main.js              # UI Interactivity (No sensitive crypto logic in JS)
│
├── storage/                         # Protected File Storage (Excluded from Git)
│   ├── encrypted_media/             # AES-256-GCM Encrypted Files (*.enc)
│   └── key_storage/                 # scrypt-Encrypted Private Key PEMs (*.enc)
│
├── experiments/
│   ├── __init__.py
│   └── attack_simulations.py        # Standalone Attack Scripts for CLI Viva Demo
│
└── tests/                           # Comprehensive Test Suite (pytest)
    ├── __init__.py
    ├── test_crypto.py               # Unit Tests: AES-GCM, RSA-PSS, RSA-OAEP, scrypt
    ├── test_hashing.py              # Unit Tests: SHA-256 streaming, pHash
    ├── test_auth.py                 # Unit Tests: Argon2id, TOTP, Lockout, RBAC
    ├── test_audit_chain.py          # Unit Tests: Hash chaining & tamper detection
    └── test_routes.py               # Integration Tests: Endpoints, CSRF, IDOR check
```

---

## 12. Phased Implementation Roadmap

1. **Phase 1: Environment & Project Setup**
   - Initialize Python virtual environment.
   - Install dependencies (`cryptography`, `argon2-cffi`, `pyotp`, `imagehash`, `reportlab`, `qrcode`, `pytest`, `pip-audit`, `flask`).
   - Configure directory layout, SQLite schema (`schema.sql`), and connection manager.
2. **Phase 2: Authentication, RBAC & Dual Key Management**
   - Implement Argon2id password hashing and account lockout logic.
   - Implement TOTP MFA setup and verification using `pyotp`.
   - Implement dual RSA key pair generation.
   - Implement scrypt KDF and AES-256-GCM private key encryption at rest under `storage/key_storage/`.
3. **Phase 3: Cryptographic Primitives & Verification Engine**
   - Implement streamed SHA-256 hashing and pHash calculation.
   - Implement canonical JSON manifest builder.
   - Implement RSA-PSS manifest signing and signature verification.
   - Implement unit tests (`test_crypto.py`) to verify signing, hashing, and tampering detection.
4. **Phase 4: Symmetric Envelope Encryption & Storage**
   - Implement AES-256-GCM encryption with random 256-bit keys and fresh nonces.
   - Implement RSA-OAEP AES key wrapping with owner's public encryption key.
   - Implement zero-plaintext storage pipeline writing to `storage/encrypted_media/`.
   - Implement authenticated decryption with tag verification and SHA-256 cross-check.
5. **Phase 5: Public Verification Portal & PDF Certificates**
   - Implement public verification route accepting suspect files and Certificate IDs.
   - Implement ReportLab PDF Certificate generator with embedded QR code.
   - Build granular verdict renderer (*Authentic*, *Modified*, *Invalid Signature*, *Unknown*).
6. **Phase 6: Hash-Chained Audit Trail & Auditor Dashboard**
   - Implement SHA-256 hash-chaining engine for `audit_log` rows.
   - Implement Auditor route and interactive chain-integrity check tool.
7. **Phase 7: `SECURE_MODE` Switch & Attack Simulation Engine**
   - Build the `SECURE_MODE` toggle mechanism.
   - Implement 6 automated attack simulation scripts and UI demonstrators.
   - Verify before-and-after states for SQLi, IDOR, brute-forcing, and tampering.
8. **Phase 8: Security Auditing, Testing & Presentation Preparation**
   - Execute complete `pytest` test suite.
   - Run `pip-audit` to confirm zero dependency CVEs.
   - Prepare final project report (5-7 pages), STRIDE threat model, and demonstration slides.

---

## 13. Viva Voce & Demonstration Guide

During evaluation by Ms. Hirra Anwar and course evaluators, the team can demonstrate the project in a cohesive 10-minute flow:

1. **Architecture & Key Separation (Aarish Muhammad):**
   - Explain why dual RSA key pairs were chosen instead of reusing a single key (preventing cross-protocol attacks).
   - Demonstrate account creation, TOTP scan via Google Authenticator, and show that private keys on disk in `storage/key_storage/` are high-entropy AES ciphertext protected by scrypt.
2. **Media Registration & Certificate Issuance (Haniyya Zubair):**
   - Upload an authentic photograph (`crime_scene.jpg`).
   - Show the generated canonical manifest, SHA-256 hash, and RSA-PSS signature.
   - Show that the stored file in `storage/encrypted_media/` is completely unreadable ciphertext.
   - Open and display the generated **PDF Verification Certificate** and scan its QR code to demonstrate seamless verification linking.
3. **Public Verification & Tampering Detection (Haniyya Zubair):**
   - Open an incognito browser window (unauthenticated guest).
   - Verify the original file: Receive **Green "AUTHENTIC"** verdict.
   - Upload a tampered version of the file (1 pixel modified): Receive **Red "MODIFIED"** verdict. Explain how SHA-256 caught the byte difference while pHash diagnosed the perceptual similarity.
4. **"Before & After" Demonstrations via `SECURE_MODE` (Abdul Moiz):**
   - **Before (`SECURE_MODE = False`):** Demonstrate an IDOR attack where an attacker downloads another user's encrypted evidence by altering the URL ID.
   - **After (`SECURE_MODE = True`):** Toggle the switch; show the exact same IDOR request blocked with `403 Forbidden` and logged in the audit trail.
5. **Tamper-Evident Audit Chain Verification (Abdul Moiz & Team):**
   - Log in as the `Auditor`. Run the cryptographic chain integrity verification tool (all hashes valid).
   - Manually edit a single character in the SQLite database file; re-run the verifier to prove that MediaGuard immediately flags the exact corrupted log index.
6. **Code & Dependency Health (Abdul Moiz):**
   - Run `pytest` in terminal (100% pass rate).
   - Run `pip-audit` to demonstrate zero known vulnerabilities in third-party libraries.

---
*End of Master Blueprint — MediaGuard Secure Media Authenticity & Integrity Verification System.*
