# Task 9 Brief: Tactile Client-Side Interactions & Telemetry Scripts (main.js)

**Repository Path:** `d:\Projects\Unii\IS Project`
**File to Modify:**
- `app/static/js/main.js`
- Optionally check: `app/static/css/style.css` (for any animation classes like `.copied-flash` or `.laser-scan`)

**Requirements:**
1. In `app/static/js/main.js`:
   - Retain and export all functions tested by `test_main_js_exists_and_contains_event_handlers`:
     `initAlertDismissal`, `initFileInputs`, `initDropzones`, `initCopyButtons`.
   - Enhance `initCopyButtons`:
     - Clicking any `.btn-copy-digest`, `.hash-badge`, or copy trigger copies the text to clipboard.
     - Adds a tactile `.copied-flash` CSS class (white-hot flash).
     - Temporarily changes text to `[COPIED // 256-BIT]` for 1.8s, then smoothly reverts.
   - Enhance `initDropzones`:
     - Dragover/dragenter adds `.dragover` and triggers active laser sweep animation.
     - When file is dropped, reads file name and size, sniffs file extension, and displays immediate tactical telemetry readout (`INGESTED: filename (size)`).
   - Add `initTotpInputs`:
     - Handles 6-character monospace TOTP inputs (if individual character apertures exist or numeric input), automatically advancing focus and handling backspace.
   - Dismiss alerts using class toggling (`.alert-dismissing`) with CSS keyframes instead of inline style mutations where possible.
   - ZERO hardcoded localhost: all fetch/API calls strictly relative.
2. Run tests: `python -m pytest tests/test_frontend.py -v`.
3. Commit: `git add app/static/js/main.js app/static/css/style.css && git commit -m "feat(ui): implement tactile clipboard flash, laser dropzone telemetry, and totp cursor advance"`.
4. Write report to `d:\Projects\Unii\IS Project\.superpowers\sdd\task-9-report.md`.
