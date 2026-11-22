# MediaGuard – The Complete Teammate's Explainer Guide
## High-Level Architecture, Frontend Walkthrough & Step-by-Step Cryptographic Guide

---

## Welcome to MediaGuard!
This guide is written specifically for you as a **semi-technical teammate**. If you understand the basics of passwords, hashing, and encryption, but want to clearly understand:
- How the user interface (Frontend) looks and behaves,
- What happens behind the scenes in Python on every click,
- What files, keys, and tokens are generated,
- Where everything is saved in the database and filesystem,
- And how a real-world user story flows from start to finish...

This document explains everything step-by-step with zero fluff and simple, clear analogies.

---

## 1. Quick Analogies: The 5 Core Concepts in Plain English

Before diving into the code and screens, here are 5 quick analogies that make the entire system immediately click:

```
+----------------------------------------------------------------------------------------------------+
| 1. The Signing Pen vs. The Padlock (Dual RSA Key Pairs)                                            |
|    - Signing Key: Your official wax seal or signature pen. Only YOU can sign documents with it.   |
|      Anyone in the world can look at your official signature and confirm it's yours.              |
|    - Encryption Key: An open padlock. Anyone can snap the padlock shut around a box, but only YOU |
|      have the key to unlock it.                                                                    |
|    - Why separate them? If you use the same key for both, a smart attacker can trick you into     |
|      signing something that actually decrypts your private data. Separation keeps you safe!        |
+----------------------------------------------------------------------------------------------------+
| 2. The Armored Truck & Safe Deposit Box (Hybrid / Envelope Encryption)                            |
|    - AES-256 is an armored truck: It can carry massive freight (large 4K videos and photos) at     |
|      supersonic speed. But it needs a secret key to unlock the cargo door.                         |
|    - RSA is a heavy vault: It is impenetrable, but too small and slow to fit a video inside.       |
|    - The Solution: We put the video in the armored truck (AES), lock it with a random AES key,    |
|      and then put that tiny AES key inside the RSA vault (RSA-OAEP). Fast AND safe!                |
+----------------------------------------------------------------------------------------------------+
| 3. DNA Test vs. Facial Recognition (SHA-256 vs. pHash)                                            |
|    - SHA-256 is a DNA test: If even a single atom or bit changes, the test fails completely.      |
|    - pHash is Facial Recognition: If someone changes their shirt, puts on glasses, or re-saves an  |
|      image with slightly lower JPEG quality, pHash recognizes: "Hey, that's still the same photo!" |
|    - By using both, MediaGuard can tell you: "The file bytes were modified, BUT visually it is     |
|      just re-compressed" versus "Someone painted over a suspect's face!"                           |
+----------------------------------------------------------------------------------------------------+
| 4. The Wax-Sealed Chain of Letters (Hash-Chained Audit Log)                                        |
|    - Imagine a notebook where every page ends with a cryptographic stamp calculated from all the   |
|      words on that page PLUS the stamp from the previous page.                                     |
|    - If a rogue administrator tries to rip out page 3 or edit a name, the stamp on page 4, 5, and |
|      6 instantly becomes invalid. You detect tampering immediately.                                |
+----------------------------------------------------------------------------------------------------+
| 5. The Security Guard On/Off Switch (SECURE_MODE)                                                 |
|    - For our university presentation to Ms. Hirra Anwar, we need to show vulnerabilities "before"  |
|      and defenses "after".                                                                         |
|    - SECURE_MODE is our live toggle switch. When turned OFF, the security guard goes to sleep, and |
|      we can show the teacher how attacks work. When turned ON, the guard wakes up and blocks them. |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Frontend Overview: What Pages Exist & What the User Sees

MediaGuard is built with **Flask + Jinja2 Templates**, giving us clean, professional HTML/CSS pages without bloated JavaScript frameworks:

```
                                  [ LANDING PAGE ] (/)
                                         |
               +-------------------------+-------------------------+
               |                                                   |
               v                                                   v
      [ PUBLIC VERIFICATION ] (/verify)                  [ USER AUTHENTICATION ]
      - Anyone can access                                - /auth/register
      - Upload suspect file                              - /auth/login (with lockout)
      - Enter Certificate ID or scan QR                  - /auth/setup-2fa (TOTP QR)
               |                                                   |
               v                                                   v
      [ VERDICT DASHBOARD ]                              [ AUTHENTICATED DASHBOARD ]
      - Authentic (Green)                                - /media (Personal Library)
      - Modified (Red with pHash info)                   - /media/upload (Drag & Drop)
      - Invalid Signature (Red Alert)                    - /media/<id>/preview (Decrypted)
      - Unknown (Yellow)                                 - /media/<id>/certificate (PDF)
                                                                   |
                               +-----------------------------------+-----------------------------------+
                               |                                                                       |
                               v (Auditor Role)                                                        v (Admin Role)
                      [ AUDIT TRAIL ] (/audit)                                               [ ADMIN PANEL ] (/admin)
                      - View system-wide logs                                                - User management / unlocking
                      - 1-Click Chain Verification                                           - SECURE_MODE Before/After Toggle
```

### Page 1: Landing Page (`/`)
- **What you see:** A hero banner explaining MediaGuard's purpose, quick metrics (Total Registered Files, Verifications Performed), and two clear call-to-action buttons:
  1. *"Verify a File Now (Public)"* ➔ Jumps straight to the verification portal.
  2. *"Register / Login"* ➔ Takes photographers, evidence officers, and investigators to their account.

### Page 2: User Registration & 2FA Setup (`/auth/register` & `/auth/setup-2fa`)
- **What you see:** A clean registration form requesting Username, Email, and Password.
- **Immediate Next Step:** After clicking Register, the screen displays a **TOTP QR Code** and a 6-digit confirmation input:
  - The user opens Google Authenticator or Authy on their phone, scans the QR code, enters the 6-digit code, and their account is activated!

### Page 3: User Login with Brute-Force Shield (`/auth/login`)
- **What you see:** Inputs for Username, Password, and the 6-digit Authenticator Code.
- **Dynamic Feedback:** If a user enters the wrong password, a counter appears: *"Invalid credentials. Attempt 1 of 5 before account lockout."*
- If 5 failed attempts occur, the login form disables for 15 minutes, showing: *"Account locked due to multiple failed attempts. Contact Administrator."*

### Page 4: User Media Library & Dashboard (`/media`)
- **What you see:** A secure gallery and table of all media files registered by the logged-in user:
  - Thumbnail or file icon (JPG, PNG, MP4, MOV).
  - Original filename and upload date.
  - SHA-256 fingerprint badge (e.g., `a81f9c2d...`).
  - Action buttons for each file:
    - **"Download Certificate"** ➔ Downloads a signed PDF certificate with an embedded QR code.
    - **"Secure Preview / Retrieve"** ➔ Decrypts the original file in-memory and displays it.
    - **"Verify File"** ➔ Pre-fills the verification page with this file's Certificate ID.

### Page 5: Media Upload & Registration Form (`/media/upload`)
- **What you see:** A drag-and-drop upload zone supporting JPG, PNG, MP4, and MOV files.
- **Real-Time Validation:** Rejects files over 50MB and prevents unsupported file types instantly.
- **Success Screen:** Once uploaded, the screen celebrates with:
  - Green checkmark: *"Media Registered & Encrypted Successfully!"*
  - Generated **Certificate ID** (UUID).
  - Calculated **SHA-256 Hash**.
  - A one-click button: *"Download Verification Certificate (PDF)"*.

### Page 6: Public Verification Portal (`/verify`)
- **What you see:** Accessible by **anyone in the world without logging in**:
  - Input field for **Certificate ID** (or pre-filled if arrived via QR code).
  - Upload zone: *"Upload the file you wish to verify against this record"*.
  - Big button: **"Run Cryptographic Verification"**.

### Page 7: Granular Verification Result (`/verify/result`)
- **What you see:** A detailed, color-coded diagnostic card:
  - **Verdict Badge:** `AUTHENTIC` (Green), `MODIFIED` (Red), `INVALID SIGNATURE` (Dark Red), or `UNKNOWN` (Yellow).
  - **Detailed Breakdown Table:**
    - Original SHA-256 vs. Uploaded File SHA-256 (Highlighted matching or differing characters).
    - Digital Signature Status (Valid under owner's public key).
    - Perceptual Similarity Diagnostic (Hamming Distance score with plain-English explanation).
    - Owner identity and official registration timestamp.

### Page 8: Auditor Log & Chain Verifier (`/audit`)
- **Who can see it:** Only logged-in users with the **Auditor** or **Admin** role.
- **What you see:** A live table of all system activities (logins, uploads, verifications, failures).
- **The Magic Button:** At the top sits a button called **"Verify Entire Audit Chain"**. Clicking it recalculates the SHA-256 hashes linking every row. If all match, a green banner proclaims: *"Audit Log Chain Intact: Zero Tampering Detected."*

### Page 9: Admin Panel & `SECURE_MODE` Switch (`/admin`)
- **Who can see it:** Only the **Admin** (`Aarish Muhammad`).
- **What you see:** User account statuses (locked/unlocked toggles), role assignments, and the **`SECURE_MODE` master switch**:
  - A toggle with a clear badge: `SECURE_MODE: ON (Protected)` vs `SECURE_MODE: OFF (Vulnerable Demonstration Mode)`.
  - When toggled for Ms. Hirra Anwar, cards show exactly which OWASP defenses are active or disabled.

### Page 10: Attack Simulations Dashboard (`/experiments`)
- **What you see:** An interactive laboratory with 6 one-click buttons allowing the user to trigger attacks and watch the system defend itself:
  1. *"Simulate 1-Pixel Tampering Attack"*
  2. *"Simulate File Replacement Attack"*
  3. *"Simulate Signature Forgery Attack"*
  4. *"Simulate Unauthorized Decryption (Wrong Key)"*
  5. *"Simulate Ciphertext Bit-Flipping Attack"*
  6. *"Simulate IDOR Access Attempt"*

---

## 3. Step-by-Step Feature Breakdown: Under the Hood

Let's walk through every single feature like an engineer building it: what libraries are called, what gets generated, where it's stored, and how it's verified.

---

### Feature 1: User Account Registration & Key Generation

```
[ User Form: Username, Password ]
              |
              +---> Argon2id.hash(password) --------------------------> Stored in `users.password_hash`
              |
              +---> pyotp.random_base32() -----------------------------> Encrypted in `users.totp_secret`
              |
              +---> rsa.generate_private_key() [Pair 1: Signing] ------> Public Key -> `users.public_signing_key`
              +---> rsa.generate_private_key() [Pair 2: Encryption] ---> Public Key -> `users.public_encryption_key`
              |
              +---> scrypt KDF(password, salt) ------------------------> Produces 256-bit KEK
              |
              +---> AES-256-GCM.encrypt(Signing Private Key) ----------> `storage/key_storage/<uid>/signing_key.enc`
              +---> AES-256-GCM.encrypt(Encryption Private Key) -------> `storage/key_storage/<uid>/encryption_key.enc`
```

1. **Which libraries are used?**
   - `argon2-cffi` for password hashing.
   - `pyotp` and `qrcode` for Multi-Factor Authentication.
   - `cryptography.hazmat.primitives.asymmetric.rsa` for RSA key generation.
   - `cryptography.hazmat.primitives.kdf.scrypt` for key derivation.
   - `cryptography.hazmat.primitives.ciphers.aead.AESGCM` for key file encryption.

2. **What is created?**
   - An Argon2id password hash string.
   - A random Base32 TOTP secret key and its QR code image.
   - **Two separate 2048-bit RSA key pairs**:
     - Key Pair A: For digital signatures (`signing_priv`, `signing_pub`).
     - Key Pair B: For key wrapping (`encryption_priv`, `encryption_pub`).
   - A 16-byte random salt (`os.urandom(16)`).
   - A 256-bit Key Encryption Key ($KEK$) derived from the password + salt via `scrypt`.

3. **Where is it stored?**
   - **In SQLite (`users` table):** `username`, `email`, `password_hash`, `totp_secret`, `public_signing_key` (PEM string), `public_encryption_key` (PEM string), and `kdf_salt`.
   - **On the Filesystem:**
     - `storage/key_storage/<user_id>/signing_key.enc` (AES-GCM encrypted private signing key).
     - `storage/key_storage/<user_id>/encryption_key.enc` (AES-GCM encrypted private encryption key).

4. **Why is this secure?**
   - Even if an attacker steals the SQLite database file, they **cannot read the private keys** (they are on the filesystem and encrypted with AES-256).
   - Even if the attacker steals the encrypted files on disk, they cannot decrypt them without the user's master password, which is protected by the memory-hard `scrypt` algorithm.

---

### Feature 2: Media Registration & Envelope Encryption

```
[ Uploaded File: evidence.jpg ]
              |
              +---> hashlib.sha256() (streamed 64KB chunks) -----------> `sha256_hash`
              +---> imagehash.phash(PIL.Image) ------------------------> `phash` (visual fingerprint)
              |
              +---> Construct Canonical JSON Registration Manifest
              |
              +---> rsa_pss.sign(manifest, signing_private_key) -------> `digital_signature`
              |
              +---> os.urandom(32) ------------------------------------> `aes_key` (256-bit)
              +---> os.urandom(12) ------------------------------------> `nonce` (96-bit)
              |
              +---> AESGCM(aes_key).encrypt(nonce, media_bytes) -------> `storage/encrypted_media/<uuid>.enc`
              |
              +---> rsa_oaep.encrypt(encryption_public_key, aes_key) --> Stored in `media.wrapped_aes_key`
              |
              +---> ReportLab + qrcode --------------------------------> Verification Certificate PDF
              |
              +---> os.remove(unencrypted_temp_file) ------------------> ZERO PLAINTEXT RETENTION!
```

1. **Which libraries are used?**
   - `hashlib` (SHA-256 streaming).
   - `imagehash` and `Pillow` (pHash).
   - `cryptography.hazmat.primitives.asymmetric.padding` (`PSS`, `OAEP`, `MGF1`).
   - `cryptography.hazmat.primitives.ciphers.aead.AESGCM`.
   - `reportlab` and `qrcode` for PDF certificate compilation.

2. **Step-by-step what happens:**
   - **Step 2A (Streaming Hash):** The server reads the file in 64-kilobyte chunks. This means even a 500MB video will not crash the server's RAM. We get a 64-character SHA-256 string.
   - **Step 2B (Perceptual Fingerprint):** If the file is an image, `imagehash.phash` calculates a 64-bit DCT hash that captures the image's structure regardless of minor compression changes.
   - **Step 2C (The Manifest):** We build a JSON string containing the Media ID, Owner ID, filename, size, MIME type, SHA-256, pHash, and server timestamp. We sort keys alphabetically (`sort_keys=True`) so the JSON is deterministic.
   - **Step 2D (Digital Signing):** The owner's decrypted in-memory `signing_private_key` signs the manifest using **RSA-PSS**.
   - **Step 2E (Envelope Encryption):**
     - Generate a fresh 32-byte AES key and 12-byte nonce.
     - Encrypt the file bytes using AES-GCM, producing ciphertext and an authentication tag.
     - Wrap the 32-byte AES key using the owner's `encryption_public_key` with **RSA-OAEP**.
   - **Step 2F (Storage & Wipe):** The ciphertext is written to `storage/encrypted_media/<media_id>.enc`. The unencrypted file is immediately deleted using `os.remove()`.

3. **Where is it stored?**
   - **SQLite (`media` table):** `media_id`, `owner_id`, `original_filename`, `file_size`, `sha256_hash`, `phash`, `wrapped_aes_key`, `nonce`, `auth_tag`, `registration_manifest`, `digital_signature`, and `registration_timestamp`.
   - **Filesystem:** `storage/encrypted_media/<media_id>.enc`.

---

### Feature 3: The Verification Certificate (PDF + Dynamic QR Code)

```
+-------------------------------------------------------------------------------+
|                             MEDIAGUARD VERIFICATION CERTIFICATE               |
|                                                                               |
|  Certificate ID : urn:uuid:6ba7b810-9dad-11d1-80b4-00c04fd430c8               |
|  Owner          : photographer_alice (CMS: 542859)                            |
|  Original File  : crime_scene_photo.jpg (4.2 MB)                              |
|  Registered UTC : 2026-11-21 10:30:00 UTC                                     |
|                                                                               |
|  [ QR CODE ]      SHA-256 Fingerprint:                                        |
|  (Scan to verify  a81f9c2d7e8b61c5a9809b4e2f9d8a3c5b2e19d7f6a4c2e1b8a9c7d5e3f1b4a2|
|   online instantly)                                                           |
|                   Perceptual Hash: d3839c4f2e6a1b05                           |
|                   Digital Signature: RSA-PSS Validated                        |
+-------------------------------------------------------------------------------+
```

1. **Which libraries are used?**
   - `reportlab.lib.pagesizes`, `reportlab.platypus` (Canvas, Paragraph, Table, Image).
   - `qrcode` (generates the QR PNG in memory via `io.BytesIO`).

2. **How does the QR Code work?**
   - The QR code contains an absolute URL pointing to:
     `https://mediaguard.local/verify?cert_id=urn:uuid:6ba7b810-9dad-11d1-80b4-00c04fd430c8`
   - When anyone scans the QR code with their smartphone, it opens the verification portal with the Certificate ID already filled in! All they need to do is upload their copy of the file to see if it matches.

---

### Feature 4: Public Verification Engine (Dual-Check System)

```
[ Verifier uploads `suspect.jpg` + Certificate ID ]
                     |
                     +---> Calculate SHA-256(suspect.jpg)
                     +---> Calculate pHash(suspect.jpg)
                     |
                     +---> Fetch Registered Record from SQLite (Manifest, Signature, Public Key)
                     |
                     +---------------------------------------+
                     |                                       |
                     v                                       v
         [ CHECK 1: File Integrity ]             [ CHECK 2: Authenticity ]
         Compare Uploaded SHA-256                Verify RSA-PSS Signature
         against Manifest SHA-256                against Registered Manifest
                     |                                       |
                     +-------------------+-------------------+
                                         |
                                         v
                         [ CHECK 3: pHash Diagnostic ]
                         (Calculate Hamming Distance if SHA-256 fails)
                                         |
                                         v
                                  FINAL VERDICT
```

1. **How does Check 1 (File Integrity) work?**
   - The system hashes the uploaded suspect file using SHA-256.
   - It reads the `sha256_hash` stored in the registered manifest.
   - If `uploaded_hash == registered_hash`, the file bytes are **100% identical**.

2. **How does Check 2 (Signature Authenticity) work?**
   - The system retrieves the owner's `public_signing_key` and the `digital_signature`.
   - It runs `public_key.verify(digital_signature, canonical_manifest_bytes, padding.PSS(...), hashes.SHA256())`.
   - If valid, this proves mathematically that the manifest was created and approved by the owner of that private key and was never altered in the database.

3. **How does Check 3 (Perceptual pHash Diagnostic) work?**
   - If the SHA-256 hashes do not match, the system doesn't just say "failed". It calculates the **Hamming Distance** (number of differing bits) between the original pHash and the suspect pHash:
     - **Distance $\le 5$:** The image was re-compressed, metadata was stripped, or it was re-saved in Paint/Photoshop, but the visual content is untouched.
     - **Distance $> 5$:** Someone edited, cropped, or forged visual elements in the image.

---

### Feature 5: Secure Media Retrieval & Decryption

```
[ Authenticated Owner clicks "Download / Preview" ]
                     |
                     +---> Check: Is session['user_id'] == media.owner_id? (Block IDOR!)
                     |
                     +---> Retrieve owner's encrypted private key from disk
                     +---> Decrypt private key in memory using session KEK (scrypt)
                     |
                     +---> rsa_oaep.decrypt(wrapped_aes_key, private_encryption_key) -> Recovers AES key
                     |
                     +---> AESGCM(aes_key).decrypt(nonce, ciphertext, auth_tag) ------> Recovers Plaintext
                     |
                     +---> hashlib.sha256(plaintext) == manifest.sha256? -------------> Confirm Decryption
                     |
                     v
       Stream file to browser memory (send_file via BytesIO)
```

1. **Why does retrieval require authentication?**
   - Anyone can *verify* a file publicly, but **only the original owner** can view or download the decrypted original media.
2. **What if the ciphertext was tampered with on disk?**
   - If a hacker opened `storage/encrypted_media/<uuid>.enc` and flipped a single byte, the `AESGCM.decrypt()` function throws an `InvalidTag` exception.
   - The system immediately stops, refuses to output any data, and logs a high-severity security alert in the audit log!

---

### Feature 6: Hash-Chained Audit Logging (Tamper-Evident Trail)

```
Row 1: [Log ID: 1 | Action: "REGISTER" | Details: "File uploaded" | Prev Hash: "0000...0000"]
       Current Hash = SHA-256(1 + "REGISTER" + ... + "0000...0000") = "a1b2c3..."
                                                                          |
                                      +-----------------------------------+
                                      v
Row 2: [Log ID: 2 | Action: "VERIFY"   | Details: "Verdict AUTHENTIC" | Prev Hash: "a1b2c3..."]
       Current Hash = SHA-256(2 + "VERIFY" + ... + "a1b2c3...") = "d4e5f6..."
                                                                          |
                                      +-----------------------------------+
                                      v
Row 3: [Log ID: 3 | Action: "RETRIEVE" | Details: "Owner downloaded"  | Prev Hash: "d4e5f6..."]
       Current Hash = SHA-256(3 + "RETRIEVE" + ... + "d4e5f6...") = "7a8b9c..."
```

1. **How is each log row constructed?**
   - Each row contains: `log_id`, `timestamp`, `user_id`, `action`, `details`, `ip_address`, `prev_hash`, and `current_hash`.
   - The `current_hash` is calculated as:
     $$\text{SHA-256}(\text{log\_id} + \text{timestamp} + \text{action} + \text{details} + \text{prev\_hash})$$
2. **How does 1-click verification work?**
   - When the Auditor clicks *"Verify Entire Audit Chain"*, Python loops through the database rows from index 1 to $N$.
   - For every row, it recomputes the SHA-256 hash and verifies that `row[i].prev_hash == row[i-1].current_hash`.
   - If someone modified or deleted a row in the database, the chain breaks at that exact index, highlighting the tampered row in bright red!

---

### Feature 7: The `SECURE_MODE` Switch (OWASP Demonstration Engine)

```python
# config.py
SECURE_MODE = True  # Can be toggled to False from Admin Panel

# In routes/media.py
@media_bp.route('/download/<media_id>')
def download_media(media_id):
    if not config.SECURE_MODE:
        # VULNERABLE MODE: No ownership check! Allows Insecure Direct Object Reference (IDOR)
        return serve_media_insecure(media_id)
    else:
        # SECURE MODE: Strict session ownership validation
        if media.owner_id != session['user_id']:
            abort(403) # Blocked!
        return serve_media_secure(media_id)
```

During your viva with Ms. Hirra Anwar:
1. Turn `SECURE_MODE = OFF`: Show how an attacker who modifies a URL from `media_id=1` to `media_id=2` can download someone else's file (Broken Access Control).
2. Flip `SECURE_MODE = ON`: Attempt the exact same URL manipulation, and watch MediaGuard return a `403 Forbidden` error with an audit log alert!

---

## 4. Complete End-to-End Walkthrough: A Real-World Story

To understand how all these gears turn together, let's follow a complete, realistic scenario from start to finish.

```
+----------------------------------------------------------------------------------------------------+
| THE PLAYERS:                                                                                       |
| - Alice: A crime scene forensic photographer (Legitimate Media Owner).                            |
| - Bob: A court judge and prosecutor (Public Verifier).                                             |
| - Charlie: A corrupt defense associate trying to alter evidence (Malicious Attacker).             |
| - Hanya: The independent compliance auditor (Auditor).                                             |
+----------------------------------------------------------------------------------------------------+
```

### Scene 1: Alice Registers Her Account
1. Alice navigates to `https://mediaguard.local/auth/register`.
2. She enters username `alice_forensics`, email, and a strong password.
3. MediaGuard hashes her password using **Argon2id**.
4. MediaGuard generates her **Dual RSA Key Pairs** (Signing Key Pair and Encryption Key Pair).
5. MediaGuard derives a 256-bit key from her password using **scrypt**, encrypts her private keys using **AES-256-GCM**, and saves them to `storage/key_storage/alice/`.
6. Alice scans the displayed **TOTP QR Code** with Google Authenticator on her iPhone.
7. Her account is live and secured with Multi-Factor Authentication.

---

### Scene 2: Alice Registers Crime Scene Evidence
1. Alice arrives back at the station with an authentic digital photograph: `crime_scene_01.jpg`.
2. She logs into MediaGuard using her password and her 6-digit TOTP code.
3. She navigates to `/media/upload` and drags `crime_scene_01.jpg` into the upload zone.
4. **Behind the scenes in Python:**
   - MediaGuard streams the file: SHA-256 is `a81f9c2d...`, and pHash is `d3839c4f...`.
   - MediaGuard builds the canonical JSON manifest with Alice's ID, the filename, size, timestamp, and hash.
   - Alice's private signing key signs the manifest using **RSA-PSS**.
   - MediaGuard generates a random 256-bit AES key and encrypts the image using **AES-256-GCM**.
   - MediaGuard wraps that AES key using Alice's public encryption key (**RSA-OAEP**).
   - The encrypted ciphertext is stored in `storage/encrypted_media/photo_uuid.enc`.
   - The original unencrypted file `crime_scene_01.jpg` is **permanently wiped** from server disk.
   - A new row is linked in the **Hash-Chained Audit Log**.
5. Alice is handed a green confirmation screen and clicks **"Download Certificate"**.
6. MediaGuard generates and downloads `MediaGuard_Certificate_crime_scene_01.pdf` containing the provenance metadata and an embedded QR code.

---

### Scene 3: Bob Verifies the Evidence in Court
1. Alice presents her digital photograph along with the PDF Verification Certificate to Judge Bob.
2. Bob wants to confirm the photo has not been manipulated.
3. Bob does **not** have an account on MediaGuard, and he doesn't need one!
4. Bob scans the QR code on the certificate with his tablet. His browser opens:
   `https://mediaguard.local/verify?cert_id=urn:uuid:photo_uuid`
5. Bob selects the photo file given to the court and clicks **"Verify"**.
6. **Behind the scenes in Python:**
   - MediaGuard recalculates the SHA-256 hash of Bob's uploaded file.
   - MediaGuard retrieves Alice's signed manifest from the database and verifies the RSA-PSS signature using Alice's public signing key.
   - Both SHA-256 hashes match identically.
   - The signature is valid.
7. Bob's screen lights up **Green: "AUTHENTIC EVIDENCE VERIFIED"**.
8. The court accepts the evidence with 100% mathematical certainty.

---

### Scene 4: Charlie Attempts to Tamper with the Evidence
1. Corrupt defense associate Charlie obtains a copy of `crime_scene_01.jpg`.
2. Charlie opens Photoshop and subtly removes a weapon lying on the floor, saving it as `crime_scene_clean.jpg`.
3. In court, Charlie argues: *"Look at this photo, there was no weapon at the scene!"*
4. Judge Bob uploads Charlie's `crime_scene_clean.jpg` to the MediaGuard verification portal under the same Certificate ID.
5. **Behind the scenes in Python:**
   - MediaGuard computes the SHA-256 hash of Charlie's file: `7b4f1e09...`.
   - MediaGuard compares it to the registered original hash: `a81f9c2d...`.
   - **HASH MISMATCH!**
   - MediaGuard calculates the pHash Hamming distance: score is 14 (severe visual alteration).
   - Alice's digital signature on the original manifest remains valid, proving that the original record was never altered.
6. Bob's screen displays a **Bright Red Alert: "VERIFICATION FAILED: MEDIA MODIFIED / TAMPERED"**.
7. The system explicitly outputs: *"SHA-256 mismatch detected. Visual content has been significantly altered (pHash Distance: 14). Manifest signature remains valid under Alice's public key."*
8. Charlie's forgery is exposed instantly on the record!

---

### Scene 5: Auditor Hanya Audits the System
1. Compliance Officer Hanya logs in with her **Auditor** account.
2. She navigates to `/audit`.
3. She reviews the immutable log of Alice's registration, Bob's successful verification, and Charlie's failed tampering attempt.
4. Hanya clicks **"Verify Entire Audit Chain"**.
5. Python walks the cryptographic hash links from row 1 to row 500, confirming that no rogue system administrator modified any records or deleted Charlie's failed attempt.
6. A green confirmation banner displays: *"All 500 Audit Log Entries Valid & Cryptographically Intact."*

---

### Scene 6: Alice Securely Retrieves Her Original Photo
1. Three months later, Alice needs to retrieve her original high-resolution photo for another case.
2. She logs into MediaGuard and visits her personal library at `/media`.
3. She clicks **"Secure Retrieve / Decrypt"**.
4. **Behind the scenes in Python:**
   - MediaGuard verifies that `session['user_id'] == media.owner_id`.
   - MediaGuard reads Alice's encrypted private encryption key from `storage/key_storage/alice/encryption_key.enc`.
   - MediaGuard decrypts Alice's private key in server RAM using the key derived from her session password via `scrypt`.
   - Alice's private key unwraps the AES-256 key via **RSA-OAEP**.
   - MediaGuard decrypts `storage/encrypted_media/photo_uuid.enc` using **AES-256-GCM**.
   - The AES-GCM authentication tag verifies successfully (proving the ciphertext was never corrupted on disk).
   - The decrypted plaintext's SHA-256 hash is checked against the registered manifest.
5. The pristine, unencrypted original photograph is streamed directly to Alice's browser for download.

---

## 5. Summary Reference: Who Uses What Library Where?

| What We Are Doing | Library Used | Function / Class | Output / Product |
| :--- | :--- | :--- | :--- |
| **Password Hashing** | `argon2-cffi` | `PasswordHasher().hash()` | Salted, memory-hard password hash |
| **Two-Factor Auth** | `pyotp` + `qrcode` | `pyotp.TOTP()`, `qrcode.make()` | 6-digit dynamic codes + QR PNG |
| **Key Derivation (KDF)** | `cryptography` | `scrypt.Scrypt(salt, 32, n, r, p)` | 256-bit Key Encryption Key ($KEK$) |
| **Key Generation** | `cryptography` | `rsa.generate_private_key(65537, 2048)` | Dual RSA public & private key pairs |
| **Private Key Storage** | `cryptography` | `AESGCM(kek).encrypt(nonce, pem, None)` | Encrypted `.enc` key files on disk |
| **File Hashing** | `hashlib` | `hashlib.sha256().update(chunk)` | 64-character exact byte fingerprint |
| **Visual Hashing** | `imagehash` + `Pillow`| `imagehash.phash(Image.open())` | 16-character perceptual DCT hash |
| **Digital Signing** | `cryptography` | `sign(..., padding.PSS(...), hashes.SHA256())` | Non-repudiable digital signature |
| **Signature Verify** | `cryptography` | `verify(..., padding.PSS(...), hashes.SHA256())` | True / `InvalidSignature` exception |
| **Media Encryption** | `cryptography` | `AESGCM(aes_key).encrypt(nonce, data, None)`| Ciphertext + 128-bit authentication tag |
| **Key Wrapping** | `cryptography` | `encrypt(..., padding.OAEP(...))` | RSA-OAEP encrypted symmetric key |
| **PDF Certificate** | `reportlab` | `SimpleDocTemplate`, `Table`, `Image` | Verifiable PDF document with QR code |
| **Tamper-Evident Log**| `hashlib` | `sha256(prev_hash + log_data)` | Blockchain-style linked log chain |
| **Security Auditing** | `pip-audit` | CLI scan | Vulnerability report of installed packages |
| **Unit Testing** | `pytest` | Test assertions | 100% automated test coverage |

---
*End of Teammate's Explainer Guide — MediaGuard Secure Media Authenticity & Integrity Verification System.*
