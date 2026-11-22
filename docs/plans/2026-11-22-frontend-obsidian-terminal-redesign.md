# Frontend Redesign: "Obsidian & Lava Red Forensic Terminal" Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completely replace the generic "AI-vibecoded" frontend with an authoritative, high-contrast, tactile "Obsidian & Lava Red Forensic Terminal" across all 14 templates, eliminating text walls, pill buttons, and disabled input hashes while maintaining 100% test pass rate across all 105 tests.

**Architecture:** A foundation-first CSS token and component primitive rewrite (`variables.css`, `style.css`), followed by parallel workstream dispatch across three independent template tracks (Public/Verify, Identity/Vault, Governance/Lab), coordinated and audited by verification subagents, concluding with interactive telemetry scripts (`main.js`) and Playwright real-browser E2E validation.

**Tech Stack:** Semantic HTML5, Vanilla CSS3 (Custom Properties, Grid, Flexbox, Keyframes, Chamfered Clip-Paths), Vanilla JavaScript ES6+ (Zero external UI frameworks), Flask/Jinja2, Google Fonts (`Space Grotesk`, `JetBrains Mono`), Playwright E2E, Pytest.

## Global Constraints

- **Zero Inline Styles:** Never use `style="..."` in any HTML template. Every visual style must derive from CSS classes and tokens.
- **Zero Hardcoded Localhost:** All frontend URLs and links must be relative (e.g., `/verify`, `/media/upload`).
- **Strict Backward Compatibility with Test Contracts:** Preserve all input names (`name="username"`, `name="totp_code"`), button texts, and semantic test markers verified by `tests/test_frontend.py`, `tests/test_audit_routes.py`, `tests/test_secure_mode.py`, and `tests/test_simulations.py`.
- **Palette Identity:** Obsidian canvas `#050507`, Milled Chassis `#0b0c10`/`#121319`, Hairlines `#1f222e`, Lava Red `#ff2a4b`, Proof Emerald `#00e599`, Amber `#ffaa00`.
- **Typography Identity:** `Space Grotesk` (display/tactical headers), `JetBrains Mono` (telemetry, hashes, byte streams, timestamps), `Inter Tight` (crisp body).
- **Geometry Identity:** Sharp 2px radii, chamfered corner notches, tactile mechanical buttons with physical travel, zero rounded pills.
- **Copy Discipline:** Prune 80% of textbook paragraph copy. Favor concise technical statements, status indicators, and telemetry readouts.

---

## Workstream Breakdown & Parallel Architecture

```mermaid
flowchart TD
    subgraph Foundation ["Stage 1: Foundation (Sequential)"]
        T1["Task 1: Master CSS Tokens & Primitives\n(variables.css + style.css)"] --> T2["Task 2: Global Shell & Avionics Nav\n(base.html)"]
        T2 --> G1{"Gate 1: Foundation Verification\n(Tokens + Base Render + Pytest)"}
    end

    G1 --> StreamA & StreamB & StreamC

    subgraph StreamA ["Stage 2A: Public Ingress & Verification"]
        T3["Task 3: Interactive Workbench Hero\n(index.html)"] --> T4["Task 4: Public Verification & Forensic Dossier\n(verify.html + result.html)"]
    end

    subgraph StreamB ["Stage 2B: Identity & Vault Management"]
        T5["Task 5: Vault Access & Key Enrollment\n(login.html + register.html + setup_2fa.html)"] --> T6["Task 6: Evidence Ingestion & Locker\n(upload.html + library.html + preview.html)"]
    end

    subgraph StreamC ["Stage 2C: Governance, Ledger & Lab"]
        T7["Task 7: Hash-Chained Blockchain Ledger\n(audit_log.html)"] --> T8["Task 8: SOC Command Terminal & Lab\n(dashboard.html + secure_mode.html + simulations.html)"]
    end

    StreamA --> G2A{"Gate 2A: Verify Stream A"}
    StreamB --> G2B{"Gate 2B: Verify Stream B"}
    StreamC --> G2C{"Gate 2C: Verify Stream C"}

    G2A & G2B & G2C --> Integration ["Stage 3: Integration & Final Polish"]

    subgraph Integration ["Stage 3: Integration & Polish"]
        T9["Task 9: Interactive Telemetry Scripts\n(main.js)"] --> T10["Task 10: Full-Suite Pytest & Playwright E2E\n(105 Tests + Browser QA)"]
        T10 --> FinalGate{"Final Gate: Lead Auditor Approval"}
    end
```

---

## Stage 1: Foundation (Sequential)

### Task 1: Master CSS Tokens & Component Primitives

**Files:**
- Modify: `app/static/css/variables.css`
- Modify: `app/static/css/style.css`
- Test: `tests/test_frontend.py`

**Interfaces:**
- Consumes: Google Fonts (`Space Grotesk`, `JetBrains Mono`, `Inter Tight`)
- Produces: CSS custom properties (`--bg-void`, `--bg-chassis`, `--lava-core`, `--border-laser`, etc.), utility classes (`.font-mono`, `.dropzone`, `.table-vault`), component primitives (`.btn-lava`, `.card-tactical`, `.aperture-input`, `.reticle-box`, `.verdict-seal`).

- [ ] **Step 1: Write token & component assertion tests**

Inspect `tests/test_frontend.py` to ensure all existing required tokens in `test_css_variables_contain_all_design_tokens` and classes in `test_style_css_contains_all_component_classes` remain tested. Add assertions for new tactical tokens:

```python
# Add to tests/test_frontend.py
def test_tactical_obsidian_tokens_exist():
    css_path = Path(__file__).resolve().parent.parent / 'app' / 'static' / 'css' / 'variables.css'
    content = css_path.read_text(encoding='utf-8')
    tactical_tokens = ['--bg-void', '--bg-chassis', '--bg-plate', '--bg-aperture', '--lava-core', '--signal-emerald', '--signal-amber', '--font-display']
    for token in tactical_tokens:
        assert token in content, f"variables.css missing tactical token: {token}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_frontend.py::test_tactical_obsidian_tokens_exist -v`
Expected: FAIL (tactical tokens not yet in `variables.css`).

- [ ] **Step 3: Implement new design tokens in `variables.css`**

Update `app/static/css/variables.css` to redefine all color variables into the **Obsidian & Lava Red** system while preserving backward-compatible token names (`--bg-base`, `--primary`, `--font-sans`, etc.) so existing classes continue to function:

```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
  /* Obsidian Substrate */
  --bg-void: #050507;
  --bg-chassis: #0b0c10;
  --bg-plate: #121319;
  --bg-aperture: #08090d;
  --bg-subplate: #181a24;
  
  /* Backward-compatible base mappings */
  --bg-base: var(--bg-void);
  --bg-surface: var(--bg-chassis);
  --bg-elevated: var(--bg-plate);
  --bg-card: var(--bg-plate);
  
  /* Hairline Laser Rules */
  --border-laser: #1f222e;
  --border-tactical: #2b3042;
  --border-focus-laser: #ff2a4b;
  --border-subtle: var(--border-laser);
  --border-default: var(--border-tactical);
  --border-focus: var(--border-focus-laser);

  /* Tactical Lava Red Core */
  --lava-core: #ff2a4b;
  --lava-hot: #ff4765;
  --lava-ember: #b3142d;
  --lava-glow: rgba(255, 42, 75, 0.20);
  --lava-dim: rgba(255, 42, 75, 0.08);

  /* Primary backward mappings */
  --primary: var(--lava-core);
  --primary-hover: var(--lava-hot);
  --primary-glow: var(--lava-glow);

  /* Spectral Forensic Signals */
  --signal-emerald: #00e599;
  --signal-crimson: #ff2a4b;
  --signal-amber: #ffaa00;
  --signal-cyan: #00f0ff;

  --success: var(--signal-emerald);
  --success-bg: rgba(0, 229, 153, 0.08);
  --success-border: rgba(0, 229, 153, 0.3);
  --danger: var(--signal-crimson);
  --danger-bg: rgba(255, 42, 75, 0.10);
  --danger-border: rgba(255, 42, 75, 0.35);
  --warning: var(--signal-amber);
  --warning-bg: rgba(255, 170, 0, 0.08);
  --warning-border: rgba(255, 170, 0, 0.3);
  --info: var(--signal-cyan);
  --info-bg: rgba(0, 240, 255, 0.08);
  --info-border: rgba(0, 240, 255, 0.3);

  /* Titanium Typography */
  --text-pure: #ffffff;
  --text-main: #e2e4ed;
  --text-muted: #8d93a8;
  --text-dim: #4e546a;

  /* Fonts */
  --font-display: 'Space Grotesk', -apple-system, sans-serif;
  --font-sans: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Strict Mechanical Geometry (Zero Rounded Pills) */
  --radius-sm: 2px;
  --radius-md: 2px;
  --radius-lg: 3px;
  --radius-full: 2px;

  /* Elevation */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.8);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.9);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.95);
  --shadow-laser: 0 0 12px rgba(255, 42, 75, 0.35);
}
```

- [ ] **Step 4: Implement tactical component primitives in `style.css`**

Update `app/static/css/style.css` to build out tactical mechanical buttons, command aperture inputs, milled reticle panels, laser borders, and status LEDs. Ensure all required classes from `test_style_css_contains_all_component_classes` (`.card-glass`, `.btn`, `.btn-primary`, `.btn-secondary`, `.badge-status`, `.badge-authentic`, `.badge-modified`, `.input-terminal`, `.table-vault`, etc.) are implemented with the new obsidian/lava styling.

- [ ] **Step 5: Run tests to verify tokens and styles pass**

Run: `python -m pytest tests/test_frontend.py -v`
Expected: ALL PASS.

- [ ] **Step 6: Commit**

Run:
```bash
git add "IS Project/app/static/css/variables.css" "IS Project/app/static/css/style.css" "IS Project/tests/test_frontend.py"
git commit -m "style: implement obsidian and lava red master design tokens and tactical component primitives"
```

---

### Task 2: Global Shell & Avionics Navigation (`base.html`)

**Files:**
- Modify: `app/templates/base.html`
- Test: `tests/test_frontend.py`

**Interfaces:**
- Consumes: CSS tokens from Task 1, Flask session / current_user
- Produces: Avionics HUD navigation bar, operator credential plate, HUD telemetry alert intercepts, technical instrument footer.

- [ ] **Step 1: Verify current tests pass**

Run: `python -m pytest tests/test_frontend.py -k "test_home_page" -v`
Expected: PASS.

- [ ] **Step 2: Rewrite `base.html`**

Refactor `app/templates/base.html`:
- Replace generic blurred navbar with **Avionics HUD Header**:
  - Brandmark: `MEDIA_GUARD // 0xMG` with live pulsing emerald LED (`[ONLINE]`).
  - Monospace indexed flight rail links: `//01 INGRESS` (`/`), `//02 VERIFY` (`/verify`), `//03 VAULT` (`/media/`), `//04 LEDGER` (`/audit/`), `//05 MATRIX` (`/admin/secure-mode`).
  - Operator credential plate: displays `OPERATOR: [username] // CLEARANCE: [ROLE]` with mechanical tactile `[LOGOUT]` button.
- Flash messages styled as **Tactical HUD Telemetry Intercepts** with left laser accent stripes and monospace error codes (`[WARN_0x44]`, `[AUTH_FAIL]`).
- Footer transformed into an **Instrument Status Rail** with server UTC time, SHA-256 chunk engine status, zero-plaintext storage indicator, and course/NUST colophon.
- Ensure strict zero inline styles (`style="..."`).

- [ ] **Step 3: Run test to verify base render and zero inline styles**

Run: `python -m pytest tests/test_frontend.py -v`
Expected: ALL PASS.

- [ ] **Step 4: Commit**

Run:
```bash
git add "IS Project/app/templates/base.html"
git commit -m "feat(ui): convert base layout into avionics HUD navigation and telemetry status rail"
```

---

### Gate 1: Foundation Verification Checkpoint

- [ ] **Step 1: Run complete test suite**
  Run: `python -m pytest tests/ -v`
  Expected: 105 passed.
- [ ] **Step 2: Verify zero inline styles across templates**
  Run: `python -m pytest tests/test_frontend.py::test_zero_inline_styles_in_all_templates -v`
  Expected: PASS.

---

## Stage 2: Parallel Workstreams (Dispatched in Parallel)

### Stage 2A: Public Ingress & Verification

#### Task 3: Public Hero & Interactive Ingress (`index.html`)

**Files:**
- Modify: `app/templates/index.html`
- Test: `tests/test_frontend.py::test_home_page_renders_html_with_design_tokens`

**Interfaces:**
- Consumes: Task 1 CSS tokens, Task 2 `base.html`
- Produces: Asymmetric Forensic Workbench Hero, Live Cryptographic Telemetry HUD Widget, Tri-Vector Forensic Engine Schematic, NIST/OWASP Defense Matrix.

- [ ] **Step 1: Write test for new workbench elements**

Add test in `tests/test_frontend.py` verifying the landing page contains the live verification aperture and telemetry strip without breaking existing string assertions (`'MediaGuard'`, `'Cryptographic Provenance'`, etc.):

```python
def test_home_page_contains_forensic_workbench(client):
    response = client.get('/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'ZERO-TAMPER MEDIA PROVENANCE' in html or 'Cryptographic Provenance' in html
    assert 'telemetry-strip' in html or 'spec-strip' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_frontend.py::test_home_page_contains_forensic_workbench -v`
Expected: FAIL.

- [ ] **Step 3: Redesign `index.html`**

Refactor `app/templates/index.html`:
- Cut 80% of explanatory paragraphs.
- Left Flank: Space Grotesk headline `ZERO-TAMPER MEDIA PROVENANCE` with terse subhead and dual tactile action buttons: `[INITIALIZE PUBLIC VERIFICATION]` (lava red) and `[VAULT INGRESS]` (milled plate).
- Right Flank: **Live Cryptographic Telemetry HUD Widget** with active simulated chunk stream and 64-bit DCT perceptual hash matrix.
- Replace the 3-column bento grid with a **Tri-Vector Forensic Engine Schematic** (`Vector 01: Cryptographic Envelope`, `Vector 02: Dual-Check Divergence`, `Vector 03: Immutable Ledger`).
- Replace dense text with a single-line **Telemetry Spec Strip**: `[ SPEC: NIST SP 800-57 ]` · `[ STREAM: SHA-256 ]` · `[ PERCEPTION: 64-BIT DCT ]` · `[ CIPHER: AES-256-GCM ]`.
- Ensure all required text strings from `tests/test_frontend.py` (`'MediaGuard'`, `'Cryptographic Provenance'`, `'/verify'`, `'CS-353 Information Security · NUST SEECS'`) are preserved.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_frontend.py -k "test_home_page" -v`
Expected: ALL PASS.

- [ ] **Step 5: Commit**

Run:
```bash
git add "IS Project/app/templates/index.html" "IS Project/tests/test_frontend.py"
git commit -m "feat(ui): redesign landing page into asymmetric forensic workbench and telemetry schematic"
```

---

#### Task 4: Public Verification Portal & Forensic Dossier (`verify/verify.html`, `verify/result.html`)

**Files:**
- Modify: `app/templates/verify/verify.html`
- Modify: `app/templates/verify/result.html`
- Test: `tests/test_verify_routes.py`

**Interfaces:**
- Consumes: Task 1 CSS tokens, Task 2 `base.html`
- Produces: Optical Inspection Gate, Official Forensic Verification Dossier with Dual-Rail Bitstream Comparator, 64-bit DCT divergence gauge, and stamped verdict seal.

- [ ] **Step 1: Check verification route tests**

Run: `python -m pytest tests/test_verify_routes.py -v`
Expected: ALL PASS.

- [ ] **Step 2: Redesign `verify/verify.html`**

Refactor `app/templates/verify/verify.html`:
- Transform the upload box into the **Public Integrity Inspection Gate**.
- Dual input channels: Direct UUID/Certificate input well with red `❯` prompt, and drag-and-drop evidence inspection plate with animated corner brackets.
- Retain form fields (`#certificate_id`, `#verify-file`, `name="certificate_id"`, `name="media_file"`) required by tests and scripts.

- [ ] **Step 3: Redesign `verify/result.html`**

Refactor `app/templates/verify/result.html`:
- **Eradicate `<input>` form fields for hashes.** Replace with the **Dual-Rail Hexadecimal Bitstream Comparator**.
- Group the 64-character SHA-256 digests into 4-character monospace blocks (`1b76 3946 5dea ...`). Mismatched hex blocks ignite in glowing lava-red chips.
- Add the **Forensic Verdict Seal**:
  - When AUTHENTIC: Milled basalt plate with glowing emerald rule and embossed stamp `[VERDICT: 100% BITWISE AUTHENTIC // RSA-PSS VALID]`.
  - When MODIFIED: Searing lava red perimeter strobe with embossed stamp `[VERDICT: TAMPERED / HASH MISMATCH]`.
- Add **pHash Hamming Distance Gauge**: An illuminated visual bar indicating 0 to 64 bits divergence ($D_H \le 10$: Perceptually Preserved, $D_H > 10$: Substantively Altered).
- Retain all data attributes, IDs, and PDF download buttons required by test assertions.

- [ ] **Step 4: Run test to verify verification routes pass**

Run: `python -m pytest tests/test_verify_routes.py -v`
Expected: ALL PASS.

- [ ] **Step 5: Commit**

Run:
```bash
git add "IS Project/app/templates/verify/verify.html" "IS Project/app/templates/verify/result.html"
git commit -m "feat(ui): redesign verification portal and forensic dossier with dual-rail bitstream comparator"
```

---

### Stage 2B: Identity & Vault Management

#### Task 5: Vault Access & Key Enrollment (`login.html`, `register.html`, `setup_2fa.html`)

**Files:**
- Modify: `app/templates/auth/login.html`
- Modify: `app/templates/auth/register.html`
- Modify: `app/templates/auth/setup_2fa.html`
- Test: `tests/test_frontend.py`

**Interfaces:**
- Consumes: Task 1 CSS tokens, Task 2 `base.html`
- Produces: Vault Access Terminal, Identity Provisioning Chamber, Cryptographic Seed Enrollment Terminal.

- [ ] **Step 1: Check existing auth frontend tests**

Run: `python -m pytest tests/test_frontend.py -k "login or register or setup_2fa" -v`
Expected: ALL PASS.

- [ ] **Step 2: Redesign `auth/login.html`**

Refactor `app/templates/auth/login.html`:
- Style as the **Vault Credential Access Terminal** with chamfered housing and command aperture inputs (`usr:`, `pwd:`, `totp:`).
- Retain form names `username`, `password`, `totp_code`, button text `'Authenticate & Unlock Vault'`, and class `'card-glass'` to satisfy `test_login_page_renders_clean_form`.
- Add lockout telemetry alert box displaying failed attempt count (`[ATTEMPTS: 3 / 5]`).

- [ ] **Step 3: Redesign `auth/register.html`**

Refactor `app/templates/auth/register.html`:
- Style as the **Identity Provisioning Chamber**. Remove redundant card-in-card.
- Add real-time **Keypair Provisioning Readout**: `[RSA-PSS-2048: READY]`, `[RSA-OAEP-2048: READY]`, `[ARGON2ID_SALT: ARMED]`.
- Retain form names `username`, `email`, `password`, `confirm_password` and required test strings `'MediaGuard Registration'`, `'Zero-Plaintext Security'`, `'2048-bit RSA-PSS'`.

- [ ] **Step 4: Redesign `auth/setup_2fa.html`**

Refactor `app/templates/auth/setup_2fa.html`:
- Style as the **Cryptographic Seed Enrollment Terminal**.
- Invert QR code on a dark scanning plate with corner reticles.
- Build 6-character monospace aperture for TOTP verification.
- Retain required test strings `'Activate Authenticator App'`, `'/auth/totp-qr'`, `'name="code"'`, `'Verify & Activate Account'`.

- [ ] **Step 5: Run tests to verify auth suite passes**

Run: `python -m pytest tests/test_frontend.py -k "login or register or setup_2fa" -v`
Expected: ALL PASS.

- [ ] **Step 6: Commit**

Run:
```bash
git add "IS Project/app/templates/auth/"
git commit -m "feat(ui): redesign authentication, registration, and 2FA setup into tactical cryptographic terminals"
```

---

#### Task 6: Digital Evidence Ingestion & Locker (`media/upload.html`, `media/library.html`, `media/preview.html`)

**Files:**
- Modify: `app/templates/media/upload.html`
- Modify: `app/templates/media/library.html`
- Modify: `app/templates/media/preview.html`
- Test: `tests/test_media_routes.py`

**Interfaces:**
- Consumes: Task 1 CSS tokens, Task 2 `base.html`
- Produces: Optical Scanner Ingestion Aperture, Encrypted Evidence Locker Table with Active Readiness Telemetry, Decrypted Evidence Lightbox.

- [ ] **Step 1: Check media routes tests**

Run: `python -m pytest tests/test_media_routes.py -v`
Expected: ALL PASS.

- [ ] **Step 2: Redesign `media/upload.html`**

Refactor `app/templates/media/upload.html`:
- Style as the **Digital Evidence Ingestion Chamber**.
- Ingestion aperture well with corner targeting brackets and vertical laser scanning line.
- Real-time pipeline indicators: `[1. Magic Bytes] ➔ [2. SHA-256 Stream] ➔ [3. DCT pHash] ➔ [4. RSA-PSS Sign] ➔ [5. AES-256-GCM Envelope]`.
- Preserve input ID `#media-file` and form field `name="media_file"`.

- [ ] **Step 3: Redesign `media/library.html`**

Refactor `app/templates/media/library.html`:
- Style as the **Encrypted Evidence Locker**.
- Top telemetry rail: total assets, encrypted volume, ledger status.
- Empty state transformed into **Cryptographic Vault Armed State** showing AES-256-GCM online, RSA-PSS verified, and zero-plaintext storage indicator.
- Populated state: Dense tabular layout with filetype glyphs, grouped 12-char SHA-256 hex chips, pHash frequency badges, and tactile icon buttons (`[VIEW]`, `[DECRYPT]`, `[CERT]`, `[VERIFY]`).
- Preserve table class `.table-vault`.

- [ ] **Step 4: Redesign `media/preview.html`**

Refactor `app/templates/media/preview.html`:
- Style as the **Decrypted Evidence Inspection Console**.
- Left Flank: Optical Evidence Lightbox with crosshair reticles, dimension telemetry, and warning watermark `IN-MEMORY DECRYPTED VIEW // CIPHERTEXT PRESERVED ON DISK`.
- Right Flank: Cryptographic provenance plate with full SHA-256, pHash, RSA-PSS signature verification indicator, and PDF certificate export button.
- Preserve image data URL format `'data:image/png;base64,'` tested by `test_media_routes.py`.

- [ ] **Step 5: Run media tests to verify all pass**

Run: `python -m pytest tests/test_media_routes.py -v`
Expected: ALL PASS.

- [ ] **Step 6: Commit**

Run:
```bash
git add "IS Project/app/templates/media/"
git commit -m "feat(ui): redesign evidence ingestion dropzone, vault library, and decrypted inspection lightbox"
```

---

### Stage 2C: Governance, Ledger & Lab

#### Task 7: Tamper-Evident Hash-Chained Audit Ledger (`audit/audit_log.html`)

**Files:**
- Modify: `app/templates/audit/audit_log.html`
- Test: `tests/test_audit_routes.py`

**Interfaces:**
- Consumes: Task 1 CSS tokens, Task 2 `base.html`
- Produces: Blockchain Hash-Chained Ledger Console, Live Integrity Sweep HUD Controller, Genesis Anchor Seal.

- [ ] **Step 1: Check audit route tests**

Run: `python -m pytest tests/test_audit_routes.py -v`
Expected: ALL PASS.

- [ ] **Step 2: Redesign `audit/audit_log.html`**

Refactor `app/templates/audit/audit_log.html`:
- Style as the **Cryptographic Hash-Chained Blockchain Ledger Console**.
- Top controller: Tactical button `[RUN HASH-CHAIN INTEGRITY SWEEP]` with mechanical safety styling. Dynamic verification banner rendering an animated block-by-block cryptographic verification HUD.
- Ledger Table: Each row represents a cryptographic ledger block linked visually to its predecessor with vertical laser linkage lines (`::linkage::`). Explicit visualization of `Block #` | `Timestamp (UTC)` | `Operator` | `OpCode` | `Payload Digest` | `Prev_Hash ➔ Curr_Hash Anchor`.
- Genesis Block rendered with a gold/amber cryptographic genesis seal (`[BLOCK_0 // GENESIS_ANCHOR]`).
- Preserve required test strings `'Cryptographic Audit Trail'`, `'Verify Entire Audit Chain'`, and class `'table-vault'`.

- [ ] **Step 3: Run audit tests to verify all pass**

Run: `python -m pytest tests/test_audit_routes.py -v`
Expected: ALL PASS.

- [ ] **Step 4: Commit**

Run:
```bash
git add "IS Project/app/templates/audit/audit_log.html"
git commit -m "feat(ui): redesign audit trail into cryptographic hash-chained blockchain ledger console"
```

---

#### Task 8: Security Operations Center & Vulnerability Lab (`admin/dashboard.html`, `admin/secure_mode.html`, `experiments/simulations.html`)

**Files:**
- Modify: `app/templates/admin/dashboard.html`
- Modify: `app/templates/admin/secure_mode.html`
- Modify: `app/templates/experiments/simulations.html`
- Test: `tests/test_secure_mode.py`
- Test: `tests/test_simulations.py`

**Interfaces:**
- Consumes: Task 1 CSS tokens, Task 2 `base.html`
- Produces: SOC Command Terminal, OWASP Defense Hypervisor Switch, Adversarial Simulation Oscilloscope Console.

- [ ] **Step 1: Check admin and simulation tests**

Run: `python -m pytest tests/test_secure_mode.py tests/test_simulations.py -v`
Expected: ALL PASS.

- [ ] **Step 2: Redesign `admin/dashboard.html`**

Refactor `app/templates/admin/dashboard.html`:
- Style as the **Security Operations Command Terminal (SOC)**.
- 4 tactical metric readout modules: User Headcount, Threat Lockouts (pulsing red if > 0), Encrypted Vault Volume, and Global Defense Posture.
- User management table with clearance tags, failed login bar meters (`[■■■□□] 3/5`), and tactical `[RESET_LOCKOUT]` triggers.
- Preserve strings `'System Administration'` and `'User Accounts'`.

- [ ] **Step 3: Redesign `admin/secure_mode.html`**

Refactor `app/templates/admin/secure_mode.html`:
- Style as the **OWASP Defense Matrix & Dual-State Hypervisor**.
- Master switch styled as an industrial circuit breaker. When ON: calm titanium and emerald glow. When OFF: hazard perimeter striping and amber alerts.
- Matrix cards for A01 through A08 with detailed vulnerability traces vs. hardened defenses.
- Preserve required strings `'OWASP Top 10 Security Architecture Matrix'`, `'A01'` through `'A08'`, and `'Toggle SECURE_MODE'`.

- [ ] **Step 4: Redesign `experiments/simulations.html`**

Refactor `app/templates/experiments/simulations.html`:
- Style as the **Adversarial Defense Evaluation Laboratory**.
- Top console styled as an **Oscilloscope / Telemetry Command Terminal** with animated scanline beam and active attack telemetry stream.
- 6 attack cards featuring industrial arming toggles `[EXECUTE EXPLOIT VECTOR]`. Real-time stdout stream with microsecond logs and automated defense proofs.
- Preserve required strings `'Security Attack Simulation Suite'`, `'pixel_tampering'`, and `'file_replacement'`.

- [ ] **Step 5: Run tests to verify all pass**

Run: `python -m pytest tests/test_secure_mode.py tests/test_simulations.py -v`
Expected: ALL PASS.

- [ ] **Step 6: Commit**

Run:
```bash
git add "IS Project/app/templates/admin/" "IS Project/app/templates/experiments/"
git commit -m "feat(ui): redesign SOC admin terminal, OWASP hypervisor switch, and simulation laboratory"
```

---

### Gate 2: Cross-Stream Verification Gate

- [ ] **Step 1: Run complete test suite across all 105 tests**
  Run: `python -m pytest tests/ -v`
  Expected: 105 passed.
- [ ] **Step 2: Verify zero inline styles across all 14 templates**
  Run: `python -m pytest tests/test_frontend.py::test_zero_inline_styles_in_all_templates -v`
  Expected: PASS (zero inline styles).

---

## Stage 3: Integration & Final Polish

### Task 9: Interactive Telemetry Scripts (`main.js`)

**Files:**
- Modify: `app/static/js/main.js`
- Test: `tests/test_frontend.py::test_main_js_exists_and_contains_event_handlers`

**Interfaces:**
- Consumes: HTML templates, clipboard API, dropzone events
- Produces: Tactile white-flash copy confirmation (`[COPIED // 256-BIT]`), automatic 6-digit TOTP focus advance, dropzone laser sweep animations, live hash block hover diffing.

- [ ] **Step 1: Check existing JS test**

Run: `python -m pytest tests/test_frontend.py::test_main_js_exists_and_contains_event_handlers -v`
Expected: PASS.

- [ ] **Step 2: Enhance `app/static/js/main.js`**

Implement tactical client-side enhancements:
- `initCopyButtons`: Clicking any hash badge or digest triggers a brief white-hot flash (`#ffffff`) and displays `[COPIED // 256-BIT]`.
- `initDropzones`: Dragging a file over the dropzone triggers an animated laser sweep and sniffs magic bytes client-side to show immediate format feedback.
- `initTotpInputs`: For 6-digit TOTP fields, automatically advance focus to the next cell on keystroke and handle backspace navigation.
- Ensure all required functions (`initAlertDismissal`, `initFileInputs`, `initDropzones`, `initCopyButtons`) remain defined and exported to `window.MediaGuard`.

- [ ] **Step 3: Run frontend JS test**

Run: `python -m pytest tests/test_frontend.py::test_main_js_exists_and_contains_event_handlers -v`
Expected: PASS.

- [ ] **Step 4: Commit**

Run:
```bash
git add "IS Project/app/static/js/main.js"
git commit -m "feat(ui): add tactical telemetry micro-interactions, TOTP cell advance, and tactile copy flashes"
```

---

### Task 10: Full-Suite Verification & Playwright Real-Browser Validation

**Files:**
- Test: `tests/` (All 105 unit and integration tests)
- Test: `experiments/browser_e2e_qa.py` (Real-browser Playwright test script)
- Outputs: `docs/evidence/` (New browser screenshots)

**Interfaces:**
- Consumes: Running Flask application (`http://127.0.0.1:5000/`)
- Produces: Test execution logs, updated evidence screenshots of the redesigned Obsidian & Lava Red interface.

- [ ] **Step 1: Execute full pytest automated test suite**

Run: `python -m pytest tests/ -v`
Expected: 105 passed, 0 failures, 0 warnings.

- [ ] **Step 2: Execute pip-audit to confirm zero security vulnerabilities**

Run: `python -m pip_audit`
Expected: 0 vulnerabilities found.

- [ ] **Step 3: Execute Playwright real-browser E2E test script**

Run: `python experiments/browser_e2e_qa.py`
Expected:
- Registers new forensic analyst with 2FA setup.
- Ingests authentic evidence asset into encrypted vault.
- Runs public verification check on authentic asset (100% bitwise match).
- Runs public verification check on tampered asset (hash mismatch & pHash transcode alert).
- Captures fresh screenshots in `docs/evidence/`:
  - `01_home_workbench.png`
  - `02_vault_evidence_locker.png`
  - `03_verification_tamper_dossier.png`
  - `04_audit_ledger_console.png`
  - `05_simulations_laboratory.png`

- [ ] **Step 4: Inspect evidence screenshots to confirm zero AI vibecoded slop**

Verify:
- Deep obsidian void `#050507` canvas with milled basalt plates.
- Searing lava red `#ff2a4b` accents for alerts, primary actions, and tamper states.
- Sharp 2px corners and tactile mechanical buttons.
- Hash digests displayed in the Dual-Rail Hexadecimal Bitstream Comparator with zero form `<input>` clipping.
- No walls of textbook copy.

- [ ] **Step 5: Final commit**

Run:
```bash
git add "IS Project/docs/evidence/" "IS Project/experiments/browser_e2e_qa.py"
git commit -m "test(e2e): capture updated evidence screenshots validating obsidian forensic terminal redesign"
```

---

## Final Verification Checklist

- [ ] All 105 automated unit and integration tests passing (`python -m pytest tests/ -v`).
- [ ] Zero inline styles (`style="..."`) in all 14 HTML templates.
- [ ] Zero hardcoded localhost references in frontend scripts and templates.
- [ ] No truncated hashes inside HTML form `<input>` fields.
- [ ] Real-browser Playwright E2E script runs cleanly and generates evidence screenshots.
- [ ] Design completely departs from generic indigo/slate AI template slop into an authoritative Obsidian & Lava Red Forensic Terminal.
