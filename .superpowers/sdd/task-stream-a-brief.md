# Stream A Brief: Public Ingress & Verification (Tasks 3 & 4)

**Repository Path:** `d:\Projects\Unii\IS Project`
**Templates to Redesign:**
- `app/templates/index.html` (Task 3)
- `app/templates/verify/verify.html` (Task 4)
- `app/templates/verify/result.html` (Task 4)

**Requirements for Task 3 (`index.html`):**
1. Convert the landing page into the **Asymmetric Forensic Workbench**:
   - Left Flank: Space Grotesk headline `ZERO-TAMPER MEDIA PROVENANCE`. Terse subhead: *"Bit-level SHA-256 verification and 64-bit DCT perceptual hash dual-check engine. Cryptographic certainty for legal evidence and high-assurance assets."*
   - Two tactile buttons: `[INITIALIZE PUBLIC VERIFICATION]` (`/verify`) and `[VAULT INGRESS]` (`/auth/login` or `/media`).
   - Right Flank: **Live Cryptographic Telemetry HUD Widget** with active simulated chunk stream and 64-bit DCT frequency matrix with live zero-divergence readouts.
2. Cut 80% of textbook paragraph copy.
3. Replace 3-card bento with **Tri-Vector Forensic Engine Schematic**:
   - `Vector 01: Cryptographic Envelope (AES-GCM / RSA-OAEP)`
   - `Vector 02: Dual-Check Divergence (SHA-256 + 64-bit DCT pHash)`
   - `Vector 03: Immutable Ledger (SHA-256 Chained Blocks)`
4. Single-line **Telemetry Spec Strip**: `[ SPEC: NIST SP 800-57 ]` · `[ STREAM: SHA-256 ]` · `[ PERCEPTION: 64-BIT DCT ]` · `[ CIPHER: AES-256-GCM ]`.
5. NIST / OWASP Defense Matrix technical flow diagram.
6. Crucial test contracts: preserve strings: `'MediaGuard'`, `'Cryptographic Provenance'`, `'/verify'`, `'CS-353 Information Security · NUST SEECS'`.

**Requirements for Task 4 (`verify/verify.html` and `verify/result.html`):**
1. `verify/verify.html`:
   - Redesign into **Public Integrity Inspection Gate**.
   - Dual ingress: direct Certificate UUID input aperture with red `❯` prompt, and drag-and-drop evidence plate with laser corner brackets.
   - Retain IDs: `#certificate_id`, `#verify-file`, name attributes `certificate_id`, `media_file`.
   - Preserve test strings: `'Public Verification Portal'`.
2. `verify/result.html`:
   - **ERADICATE `<input>` form fields for hashes.** Replace with the **Dual-Rail Hexadecimal Bitstream Comparator**.
   - Group the 64-character SHA-256 digests into 4-character monospace blocks (`1b76 3946 5dea ...`). Highlight mismatched blocks with glowing lava-red chips.
   - Add **Forensic Verdict Seal**:
     - When AUTHENTIC: Milled basalt plate with glowing emerald rule and embossed stamp `[VERDICT: 100% BITWISE AUTHENTIC // RSA-PSS VALID]`.
     - When MODIFIED: Searing lava red perimeter strobe with embossed stamp `[VERDICT: TAMPERED / HASH MISMATCH]`.
   - Add **pHash Hamming Distance Gauge**: Illuminated visual bar from 0 to 64 bits ($D_H \le 10$: Perceptually Preserved, $D_H > 10$: Substantively Altered).
   - Retain all data attributes, PDF download button, and certificate UUID display.

**Constraints:**
- STRICT ZERO INLINE STYLES (`style="..."`).
- Run tests: `python -m pytest tests/test_frontend.py tests/test_verify_routes.py -v`.
- Commit changes.
- Write report to: `d:\Projects\Unii\IS Project\.superpowers\sdd\stream-a-report.md`.
