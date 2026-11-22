# Task 2 Brief: Global Shell & Avionics Navigation (base.html)

**Repository Path:** `d:\Projects\Unii\IS Project`
**File to Modify:**
- `app/templates/base.html`
- Optionally check: `app/static/css/style.css` (for any extra helper classes needed for the HUD header/footer)

**Requirements:**
1. Refactor `app/templates/base.html` into the **Avionics HUD Navigation**:
   - Brandmark: Tactical angular monospace logo `MEDIA_GUARD // 0xMG` with a live pulsing emerald LED dot (`[ONLINE]`). Retain `nav-brand` class and `MediaGuard` text for tests.
   - Monospace flight rail links:
     - `//01 INGRESS` (link to `/`, retain class `nav-link`)
     - `//02 VERIFY` (link to `/verify`, retain class `nav-link`)
     - When authenticated:
       - `//03 VAULT` (link to `/media`, retain class `nav-link`)
       - `//04 INGEST` (link to `/media/upload`, retain class `nav-link`)
       - If Auditor/Admin: `//05 LEDGER` (link to `/audit`, retain class `nav-link`)
       - If Admin: `//06 ADMIN` (link to `/admin`, retain class `nav-link`)
       - `//07 LAB` (link to `/experiments`, retain class `nav-link`)
   - Operator Credential Plate:
     - When authenticated: `OPERATOR: [{{ session.get('username') }}] // ROLE: [{{ session.get('role') }}]` with tactile mechanical `[LOGOUT]` button (`btn btn-secondary btn-sm`).
     - When unauthenticated: `[LOGIN]` (`btn btn-outline btn-sm`) and `[REGISTER]` (`btn btn-primary btn-sm`).
2. Flash notifications styled as **Tactical HUD Telemetry Intercepts**:
   - Left laser accent stripe, monospace error code prefixes (`[ALERT_LOG]`), tactile close button.
   - Retain classes: `.alert-container`, `.alert`, `.alert-danger`, `.alert-success`, `.alert-warning`, `.alert-info`.
3. Site Footer styled as an **Instrument Status Rail**:
   - Display system telemetry status (`[ENGINE: SHA-256 STREAMED]`, `[CIPHER: AES-256-GCM]`, `[STORAGE: ZERO-PLAINTEXT]`).
   - Retain required test string: `CS-353 Information Security · NUST SEECS` and `MediaGuard`.
4. STRICT INVARIANT: ZERO INLINE STYLES (`style="..."`).
5. Run tests: `python -m pytest tests/test_frontend.py -v`.
6. Commit: `git add app/templates/base.html app/static/css/style.css && git commit -m "feat(ui): convert base layout into avionics HUD navigation and telemetry status rail"`.
