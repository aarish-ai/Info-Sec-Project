# Stream C Brief: Governance, Ledger & Lab (Tasks 7 & 8)

**Repository Path:** `d:\Projects\Unii\IS Project`
**Templates to Redesign:**
- `app/templates/audit/audit_log.html` (Task 7)
- `app/templates/admin/dashboard.html` (Task 8)
- `app/templates/admin/secure_mode.html` (Task 8)
- `app/templates/experiments/simulations.html` (Task 8)

**Requirements for Task 7 (`audit/audit_log.html`):**
1. Style as the **Cryptographic Hash-Chained Blockchain Ledger Console**:
   - Top controller: Tactical button `[RUN HASH-CHAIN INTEGRITY SWEEP]` with mechanical safety styling. Dynamic verification banner rendering an animated block-by-block cryptographic verification HUD.
   - Ledger Table: Each row represents a cryptographic ledger block linked visually to its predecessor with vertical laser linkage lines (`::linkage::`). Explicit visualization of `Block #` | `Timestamp (UTC)` | `Operator` | `OpCode` | `Payload Digest` | `Prev_Hash ➔ Curr_Hash Anchor`.
   - Genesis Block rendered with a gold/amber cryptographic genesis seal (`[BLOCK_0 // GENESIS_ANCHOR]`).
   - Preserve required test strings: `'Cryptographic Audit Trail'`, `'Verify Entire Audit Chain'`, and class `'table-vault'`.

**Requirements for Task 8 (Admin & Simulations):**
1. `admin/dashboard.html`:
   - Style as the **Security Operations Command Terminal (SOC)**.
   - 4 tactical metric readout modules: User Headcount, Threat Lockouts (pulsing red if > 0), Encrypted Vault Volume, and Global Defense Posture.
   - User management table with clearance tags, failed login bar meters (`[■■■□□] 3/5`), and tactical `[RESET_LOCKOUT]` triggers.
   - Preserve strings: `'System Administration'`, `'User Accounts'`.
2. `admin/secure_mode.html`:
   - Style as the **OWASP Defense Matrix & Dual-State Hypervisor**.
   - Master switch styled as an industrial circuit breaker. When ON: calm titanium and emerald glow. When OFF: hazard perimeter striping and amber alerts.
   - Matrix cards for A01 through A08 with detailed vulnerability traces vs. hardened defenses.
   - Preserve required strings: `'OWASP Top 10 Security Architecture Matrix'`, `'A01'` through `'A08'`, and `'Toggle SECURE_MODE'`.
3. `experiments/simulations.html`:
   - Style as the **Adversarial Defense Evaluation Laboratory**.
   - Top console styled as an **Oscilloscope / Telemetry Command Terminal** with animated scanline beam and active attack telemetry stream.
   - 6 attack cards featuring industrial arming toggles `[EXECUTE EXPLOIT VECTOR]`. Real-time stdout stream with microsecond logs and automated defense proofs.
   - Preserve required strings: `'Security Attack Simulation Suite'`, `'pixel_tampering'`, and `'file_replacement'`.

**Constraints:**
- STRICT ZERO INLINE STYLES (`style="..."`).
- Run tests: `python -m pytest tests/test_audit_routes.py tests/test_secure_mode.py tests/test_simulations.py -v`.
- Commit changes.
- Write report to: `d:\Projects\Unii\IS Project\.superpowers\sdd\stream-c-report.md`.
