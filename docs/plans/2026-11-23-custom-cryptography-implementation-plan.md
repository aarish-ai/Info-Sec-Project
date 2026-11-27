# Custom Cryptography Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Feasibility Assessment & Complexity Demarcation

### 1. Is this possible and easy to implement given that the project is already built?
**YES, it is completely feasible and safe to implement.** 
Because MediaGuard was architected with a strict separation of concerns, all cryptographic operations are encapsulated in `app/core/` (`hashing.py`, `ciphers.py`, `signatures.py`, `totp_manager.py`, and `audit_chain.py`). The Flask controllers and templates only call high-level interface functions (e.g., `compute_streamed_sha256()`, `compute_phash()`, `verify_totp_code()`). 
Furthermore, the project possesses an automated test suite of **106 tests**; by applying **Test-Driven Development (TDD)**, we can write unit tests for the scratch implementations first, replace the internal cryptographic engines, and guarantee that not a single application flow, database record, or route is broken.

### 2. Specific Areas Implemented From Scratch (Pure Python, Zero Crypto Libraries)
The following modules will have their third-party library dependencies removed and replaced with custom mathematical implementations:
1. **Custom SHA-256 Engine (FIPS 180-4 compliant):**
   - Implemented in `app/core/custom_crypto/sha256.py`.
   - Full 64-round compression loop, message schedule expansion ($W_0 \dots W_{63}$), initial hash words ($H_0 \dots H_7$), round constants ($K_0 \dots K_{63}$), bitwise functions (`Ch`, `Maj`, $\Sigma_0$, $\Sigma_1$, $\sigma_0$, $\sigma_1$), 512-bit block padding, and streaming chunk updates.
   - **Replaces:** `hashlib.sha256` in both `hashing.py` and `audit_chain.py`.
2. **Custom HMAC Engine (RFC 2104 compliant):**
   - Implemented in `app/core/custom_crypto/hmac.py`.
   - Key-Hash Message Authentication Code using inner/outer padding ($K \oplus ipad$ and $K \oplus opad$) coupled with custom SHA-256 and custom SHA-1.
   - **Replaces:** standard library `hmac` for OTP and token generation.
3. **Custom RFC 6238 TOTP & RFC 4226 HOTP Engine:**
   - Implemented in `app/core/custom_crypto/totp.py`.
   - Custom Base32 secret decoder/encoder, 30-second time-step interval counter ($T = \lfloor t / 30 \rfloor$), HMAC-SHA1 dynamic truncation, and 6-digit zero-padded integer extraction.
   - **Replaces:** `pyotp` library completely.
4. **Custom 2D-DCT Perceptual Hashing (pHash):**
   - Implemented in `app/core/custom_crypto/phash.py`.
   - Grayscale 32x32 image reduction, 2D Discrete Cosine Transform (DCT) matrix transformation, 8x8 low-frequency matrix extraction (excluding DC component), median calculation, and 64-bit binary hash derivation.
   - Pure bitwise XOR and Hamming distance computation.
   - **Replaces:** `imagehash` library completely.
5. **Custom Symmetric Block Cipher (AES-256-CTR + HMAC-SHA256 AEAD):**
   - Implemented in `app/core/custom_crypto/aes.py`.
   - Pure Python Rijndael cipher core: SubBytes (S-box), ShiftRows, MixColumns, AddRoundKey, KeyExpansion (14 rounds, 60 32-bit words), and Counter (CTR) mode stream generation.
   - Coupled with Encrypt-then-MAC (HMAC-SHA256) for authenticated symmetric encryption.

### 3. Specific Sections Retaining Built-In / Standard Libraries ("Where It Gets Too Complicated")
As permitted by the design brief, the following areas retain battle-tested libraries because implementing them from scratch is either computationally prohibitive in pure Python, risks critical side-channel vulnerabilities, or involves massive external wire formats:
1. **2048-bit RSA Prime Generation & Key Serialization (`cryptography.hazmat.primitives.asymmetric.rsa`):**
   - *Why too complicated:* Generating two cryptographically secure 1024-bit primes ($p, q$) using the Miller-Rabin primality test in pure Python takes 5 to 45 seconds per keypair without C extensions. Running this during user registration would cause Flask HTTP requests to time out. Furthermore, serializing keys into standard ASN.1 DER / PEM PKCS#8 structures requires a full X.509 ASN.1 parser.
2. **RSA-PSS & RSA-OAEP Padding Mathematics (`cryptography.hazmat.primitives.asymmetric.padding`):**
   - *Why too complicated:* While modular exponentiation ($c = m^e \pmod n$) is straightforward, the Optimal Asymmetric Encryption Padding (OAEP) and Probabilistic Signature Scheme (PSS) require complex Mask Generation Functions (MGF1) and random salt masking to prevent chosen-ciphertext attacks. Retaining the library padding ensures standards compliance and zero timing leakage.
3. **Memory-Hard Password Hashing: Argon2id (`argon2-cffi`):**
   - *Why too complicated:* Argon2id won the Password Hashing Competition specifically because its memory-hard algorithm resists GPU/ASIC attacks through multi-pass lane permutations across tens of megabytes of RAM. A pure Python implementation would take over 10 seconds per login attempt.

---

**Goal:** Implement clean, pure-Python, zero-library cryptographic engines for SHA-256, HMAC, RFC 6238 TOTP, 2D-DCT pHash, and AES-256 symmetric cipher, while preserving existing function signatures and passing 100% of the 106 automated tests without regressions.

**Architecture:** Create a standalone package `app/core/custom_crypto/` containing pure mathematical implementations. Refactor `app/core/hashing.py`, `app/core/totp_manager.py`, `app/core/audit_chain.py`, and `app/core/ciphers.py` to use these custom engines via identical API boundaries.

**Tech Stack:** Pure Python 3 (built-in `math`, `struct`, `os.urandom`), Pytest, Playwright E2E.

## Global Constraints

- **Strict TDD Compliance:** For every custom cryptographic algorithm, write a failing unit test asserting known NIST / RFC test vectors BEFORE implementing the production algorithm.
- **Interface Invariance:** Never change the signature or return type of public core functions (`compute_streamed_sha256`, `compute_phash`, `generate_totp_secret`, `verify_totp_code`, `encrypt_media_envelope`, `decrypt_media_envelope`).
- **Zero Regressions:** All 106 existing unit and integration tests must pass with zero failures.
- **NIST / RFC Conformance:**
  - Custom SHA-256 must match FIPS 180-4 test vectors bit-for-bit.
  - Custom HMAC must match RFC 2202 test vectors bit-for-bit.
  - Custom TOTP must generate valid 6-digit tokens compatible with standard Google Authenticator / RFC 6238.

---

## Task Decomposition

### Task 1: Custom Pure-Python SHA-256 Engine (FIPS 180-4)

**Files:**
- Create: `app/core/custom_crypto/__init__.py`
- Create: `app/core/custom_crypto/sha256.py`
- Create: `tests/test_custom_sha256.py`
- Modify: `app/core/hashing.py`
- Modify: `app/core/audit_chain.py`

**Interfaces:**
- Consumes: `bytes`, `str`, binary streams
- Produces: `CustomSHA256` class with `.update(chunk: bytes)` and `.hexdigest() -> str`

- [ ] **Step 1: Write failing unit test for CustomSHA256 (TDD RED)**

Create `tests/test_custom_sha256.py` with official NIST FIPS 180-4 test vectors:

```python
import pytest
from app.core.custom_crypto.sha256 import CustomSHA256

def test_custom_sha256_empty_string():
    # NIST test vector for empty string
    h = CustomSHA256()
    assert h.hexdigest() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def test_custom_sha256_standard_vector():
    # NIST test vector for "abc"
    h = CustomSHA256(b"abc")
    assert h.hexdigest() == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

def test_custom_sha256_streaming_chunks():
    # Test incremental streaming chunks
    h = CustomSHA256()
    h.update(b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq")
    assert h.hexdigest() == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_custom_sha256.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'app.core.custom_crypto').

- [ ] **Step 3: Implement `CustomSHA256` in pure Python**

Create `app/core/custom_crypto/__init__.py` and `app/core/custom_crypto/sha256.py`:
- Initialize constants: $K_0 \dots K_{63}$ and initial hash values $H_0 \dots H_7$.
- Implement bitwise operators: right rotate `rotr(x, n)`, `Ch(x, y, z)`, `Maj(x, y, z)`, $\Sigma_0, \Sigma_1, \sigma_0, \sigma_1$.
- Implement message schedule padding: append `0x80`, pad with zeros to 56 mod 64, append 64-bit big-endian length.
- Implement 64-round compression loop over 512-bit (64-byte) blocks.
- Provide streaming `.update(data: bytes)` and `.hexdigest() -> str`.

- [ ] **Step 4: Run test to verify it passes (TDD GREEN)**

Run: `python -m pytest tests/test_custom_sha256.py -v`
Expected: 3 passed.

- [ ] **Step 5: Integrate CustomSHA256 into `hashing.py` and `audit_chain.py`**

In `app/core/hashing.py`:
- Replace `hasher = hashlib.sha256()` with `hasher = CustomSHA256()`.
In `app/core/audit_chain.py`:
- Replace `hashlib.sha256(entry_str.encode('utf-8')).hexdigest()` with `CustomSHA256(entry_str.encode('utf-8')).hexdigest()`.

- [ ] **Step 6: Run existing hashing and audit chain tests**

Run: `python -m pytest tests/test_hashing.py tests/test_audit_chain.py tests/test_audit_routes.py -v`
Expected: ALL PASS.

- [ ] **Step 7: Commit**

Run:
```bash
git add app/core/custom_crypto/ tests/test_custom_sha256.py app/core/hashing.py app/core/audit_chain.py
git commit -m "feat(crypto): implement pure Python FIPS 180-4 custom SHA-256 and integrate into hashing and audit ledger"
```

---

### Task 2: Custom Pure-Python RFC 2104 HMAC & RFC 6238 TOTP Engine

**Files:**
- Create: `app/core/custom_crypto/hmac.py`
- Create: `app/core/custom_crypto/totp.py`
- Create: `tests/test_custom_totp.py`
- Modify: `app/core/totp_manager.py`

**Interfaces:**
- Consumes: `CustomSHA256`, SHA-1 math, system time
- Produces: `CustomHMAC(key, message, hash_func)`, `CustomTOTP(secret)` with `.now()`, `.verify(code, valid_window)`, `.provisioning_uri()`

- [ ] **Step 1: Write failing unit test for Custom HMAC and TOTP (TDD RED)**

Create `tests/test_custom_totp.py`:

```python
import time
import pytest
from app.core.custom_crypto.hmac import custom_hmac_sha1
from app.core.custom_crypto.totp import CustomTOTP, generate_base32_secret

def test_custom_hmac_sha1_rfc2202_vector():
    # RFC 2202 Test Case 2
    key = b"Jefe"
    data = b"what do ya want for nothing?"
    digest = custom_hmac_sha1(key, data)
    assert digest.hex() == "effcdf6ae5eb2fa2d27416d5f184df9c259a7c79"

def test_custom_totp_generation_and_verification():
    secret = generate_base32_secret()
    totp = CustomTOTP(secret)
    code = totp.now()
    assert len(code) == 6
    assert code.isdigit()
    assert totp.verify(code, valid_window=1) is True
    assert totp.verify("000000" if code != "000000" else "111111", valid_window=0) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_custom_totp.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'app.core.custom_crypto.hmac').

- [ ] **Step 3: Implement pure Python RFC 2104 HMAC and RFC 6238 TOTP**

In `app/core/custom_crypto/hmac.py`:
- Implement standard HMAC inner/outer pad hashing:
  $$ipad = \text{0x36} \times 64, \quad opad = \text{0x5C} \times 64$$
  $$HMAC(K, M) = H((K' \oplus opad) \parallel H((K' \oplus ipad) \parallel M))$$
- Implement SHA-1 160-bit compression for RFC 4226 compatibility.

In `app/core/custom_crypto/totp.py`:
- Implement Base32 decoder/encoder (RFC 4648).
- Implement HOTP dynamic truncation:
  - Offset = last 4 bits of HMAC digest.
  - Extract 4 bytes from offset, mask with `0x7FFFFFFF`, modulo $10^6$, zero-pad to 6 digits.
- Implement TOTP time counter: $T = \lfloor t / 30 \rfloor$ and clock drift window verification (`for offset in [-valid_window, 0, +valid_window]`).

- [ ] **Step 4: Run test to verify it passes (TDD GREEN)**

Run: `python -m pytest tests/test_custom_totp.py -v`
Expected: 2 passed.

- [ ] **Step 5: Refactor `app/core/totp_manager.py` to use `CustomTOTP`**

In `app/core/totp_manager.py`:
- Remove `import pyotp`.
- Replace `pyotp.random_base32()` with `generate_base32_secret()`.
- Replace `pyotp.TOTP(secret)` with `CustomTOTP(secret)`.
- Keep `qrcode` strictly for PNG generation.

- [ ] **Step 6: Run existing auth and TOTP test suite**

Run: `python -m pytest tests/test_auth_routes.py tests/test_frontend.py -k "totp or 2fa" -v`
Expected: ALL PASS.

- [ ] **Step 7: Commit**

Run:
```bash
git add app/core/custom_crypto/hmac.py app/core/custom_crypto/totp.py tests/test_custom_totp.py app/core/totp_manager.py
git commit -m "feat(crypto): implement pure Python RFC 2104 HMAC and RFC 6238 TOTP, removing pyotp dependency"
```

---

### Task 3: Custom Pure-Python 2D-DCT Perceptual Hashing (pHash)

**Files:**
- Create: `app/core/custom_crypto/phash.py`
- Create: `tests/test_custom_phash.py`
- Modify: `app/core/hashing.py`

**Interfaces:**
- Consumes: PIL Image (for raw pixel dimensions/grayscale sampling only)
- Produces: `custom_dct_phash(img) -> str` (16-char hex string) and `custom_hamming_distance(h1, h2) -> int`

- [ ] **Step 1: Write failing unit test for custom pHash (TDD RED)**

Create `tests/test_custom_phash.py`:

```python
from PIL import Image
from app.core.custom_crypto.phash import custom_dct_phash, custom_hamming_distance

def test_custom_dct_phash_deterministic():
    img = Image.new("L", (64, 64), color=128)
    h1 = custom_dct_phash(img)
    h2 = custom_dct_phash(img)
    assert len(h1) == 16
    assert h1 == h2

def test_custom_phash_distance_identical_and_divergent():
    h1 = "856a3a3e6bc53a94"
    assert custom_hamming_distance(h1, h1) == 0
    h2 = "856a3a3e6bc53a95" # 1 bit difference
    assert custom_hamming_distance(h1, h2) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_custom_phash.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'app.core.custom_crypto.phash').

- [ ] **Step 3: Implement 2D Discrete Cosine Transform pHash in pure Python**

In `app/core/custom_crypto/phash.py`:
- Resize input image to 32x32 grayscale.
- Implement 1D/2D Discrete Cosine Transform (DCT-II):
  $$F(u, v) = \alpha(u)\alpha(v) \sum_{x=0}^{N-1}\sum_{y=0}^{N-1} f(x, y) \cos\left[\frac{(2x+1)u\pi}{2N}\right] \cos\left[\frac{(2y+1)v\pi}{2N}\right]$$
- Extract the top-left 8x8 low-frequency coefficients (ignoring DC coefficient at (0,0)).
- Compute the median of the 64 coefficients.
- Construct 64-bit integer (bit = 1 if $F(u, v) > \text{median}$ else 0).
- Format into 16-character hexadecimal string.
- Implement `custom_hamming_distance(h1, h2)` via XOR and bit count.

- [ ] **Step 4: Run test to verify it passes (TDD GREEN)**

Run: `python -m pytest tests/test_custom_phash.py -v`
Expected: 2 passed.

- [ ] **Step 5: Refactor `app/core/hashing.py` to use custom pHash**

In `app/core/hashing.py`:
- Remove `import imagehash`.
- Replace `imagehash.phash(img)` with `custom_dct_phash(img)`.
- Use `custom_hamming_distance` for `compute_phash_distance`.

- [ ] **Step 6: Run existing hashing tests**

Run: `python -m pytest tests/test_hashing.py -v`
Expected: ALL PASS.

- [ ] **Step 7: Commit**

Run:
```bash
git add app/core/custom_crypto/phash.py tests/test_custom_phash.py app/core/hashing.py
git commit -m "feat(crypto): implement pure Python 2D-DCT perceptual hash engine, removing imagehash dependency"
```

---

### Task 4: Custom Pure-Python Symmetric Cipher Engine (AES-256-CTR + HMAC-SHA256)

**Files:**
- Create: `app/core/custom_crypto/aes.py`
- Create: `tests/test_custom_aes.py`
- Modify: `app/core/ciphers.py`

**Interfaces:**
- Consumes: 32-byte AES key, 12-byte / 16-byte nonce, raw plaintext bytes
- Produces: `CustomAES256` class with `.encrypt_block(block: bytes)`, Counter mode stream encryption/decryption, and Encrypt-then-MAC authentication.

- [ ] **Step 1: Write failing unit test for Custom AES-256 (TDD RED)**

Create `tests/test_custom_aes.py` with standard NIST FIPS 197 AES-256 test vectors:

```python
import os
import pytest
from app.core.custom_crypto.aes import CustomAES256, aes_256_ctr_encrypt, aes_256_ctr_decrypt

def test_aes_256_single_block_known_answer():
    # NIST FIPS 197 AES-256 test vector
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    expected_cipher = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")
    
    cipher = CustomAES256(key)
    result = cipher.encrypt_block(plaintext)
    assert result == expected_cipher

def test_aes_256_ctr_roundtrip():
    key = os.urandom(32)
    nonce = os.urandom(12)
    message = b"MediaGuard Zero-Trust Cryptographic Evidence Asset"
    ciphertext = aes_256_ctr_encrypt(key, nonce, message)
    recovered = aes_256_ctr_decrypt(key, nonce, ciphertext)
    assert recovered == message
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_custom_aes.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'app.core.custom_crypto.aes').

- [ ] **Step 3: Implement pure Python Rijndael AES-256 and CTR mode**

In `app/core/custom_crypto/aes.py`:
- Implement Rijndael S-box, inverse S-box, and round constants `RCON`.
- Implement `KeyExpansion` for 256-bit key (14 rounds, generates 60 32-bit round words).
- Implement `SubBytes`, `ShiftRows`, `MixColumns`, `AddRoundKey`.
- Implement 128-bit block encryption `encrypt_block(block)`.
- Implement Counter Mode (CTR) streaming: generate counter blocks from 12-byte nonce + 4-byte big-endian counter, encrypt counter block with AES-256, and XOR keystream with plaintext chunks.
- Combine with Encrypt-then-MAC (using our custom `custom_hmac_sha256`) to produce a 16-byte authentication tag ensuring integrity against tampering.

- [ ] **Step 4: Run test to verify it passes (TDD GREEN)**

Run: `python -m pytest tests/test_custom_aes.py -v`
Expected: 2 passed.

- [ ] **Step 5: Integrate Custom AES into `app/core/ciphers.py`**

In `app/core/ciphers.py`:
- Use `aes_256_ctr_encrypt` with custom HMAC authentication tag in `encrypt_media_envelope`.
- Retain RSA-OAEP for asymmetric key wrapping (per Section 3 "Where It Gets Too Complicated").
- In `decrypt_media_envelope`, verify HMAC authentication tag (raising `ValueError("Invalid authentication tag: media ciphertext tampered!")`), then decrypt using `aes_256_ctr_decrypt`.

- [ ] **Step 6: Run existing cipher tests and media route tests**

Run: `python -m pytest tests/test_ciphers.py tests/test_media_routes.py -v`
Expected: ALL PASS.

- [ ] **Step 7: Commit**

Run:
```bash
git add app/core/custom_crypto/aes.py tests/test_custom_aes.py app/core/ciphers.py
git commit -m "feat(crypto): implement pure Python Rijndael AES-256 CTR cipher with HMAC authentication"
```

---

### Task 5: Full-Suite Verification & Live Workflow Validation

**Files:**
- Test: `tests/` (All 106 unit and integration tests)
- Test: `experiments/browser_e2e_qa.py` (Real-browser Playwright test script)
- Doc: `docs/evidence/`

**Interfaces:**
- Consumes: Complete MediaGuard platform
- Produces: 100% test pass confirmation, 0 regressions, clean Playwright browser execution

- [ ] **Step 1: Execute full test suite across all 106+ tests**

Run: `python -m pytest tests/ -v`
Expected: 106+ passed, 0 failures.

- [ ] **Step 2: Verify zero inline styles across all templates**

Run: `python -m pytest tests/test_frontend.py::test_zero_inline_styles_in_all_templates -v`
Expected: PASS.

- [ ] **Step 3: Run real-browser Playwright E2E automation script**

Run: `python experiments/browser_e2e_qa.py`
Expected: All 12 steps pass with 100% fidelity using the custom cryptographic engines.

- [ ] **Step 4: Update README and documentation**

Document the custom cryptographic architecture in `README.md` and `Explainer.md`, highlighting:
- Custom SHA-256 (FIPS 180-4)
- Custom HMAC (RFC 2104)
- Custom TOTP (RFC 6238)
- Custom 2D-DCT pHash
- Custom AES-256-CTR
- Strategic use of standard libraries for RSA 2048-bit prime generation and Argon2id.

- [ ] **Step 5: Commit documentation and evidence**

Run:
```bash
git add README.md Explainer.md docs/
git commit -m "docs: document custom cryptography implementation and verification evidence"
```

---

## Final Verification Checklist

- [ ] Custom SHA-256 passes all official NIST test vectors.
- [ ] Custom HMAC-SHA1 passes RFC 2202 test vectors.
- [ ] Custom TOTP generates valid codes verifiable against real RFC 6238 authenticators.
- [ ] Custom pHash computes identical 16-character hexadecimal perceptual digests and correct Hamming distances.
- [ ] Custom AES-256 passes NIST FIPS 197 known-answer test vectors.
- [ ] All 106 existing unit and integration tests pass without failures.
- [ ] Zero inline styles (`style="..."`) preserved across all templates.
- [ ] Real-browser Playwright E2E script runs cleanly and generates evidence screenshots.
