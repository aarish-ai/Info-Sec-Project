from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    flash,
    redirect,
    url_for,
    current_app
)
from config import Config
from app.database.db import get_db
from app.routes.auth import login_required, require_role
from app.core.audit_chain import append_audit_log

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def _wants_json():
    """Determine whether the request expects a JSON API response."""
    return (
        request.is_json
        or request.path.startswith('/api/')
        or 'application/json' in request.headers.get('Accept', '')
    )

OWASP_DEFENSES = [
    {
        'id': 'A01',
        'category': 'A01:2021 – Broken Access Control',
        'vulnerable': 'IDOR active: User B can download User A private media by directly requesting media_id in URL.',
        'protected': 'Server-side Ownership & strict RBAC (@require_role, 403 Forbidden). Non-owners denied access.',
        'target_endpoint': '/media/<media_id>/download'
    },
    {
        'id': 'A02',
        'category': 'A02:2021 – Cryptographic Failures',
        'vulnerable': 'Plaintext or unauthenticated storage: files written directly to disk without authenticated encryption.',
        'protected': 'Hybrid Envelope Encryption: Fresh AES-256-GCM symmetric key per file, RSA-OAEP key wrapping, scrypt KDF.',
        'target_endpoint': 'storage/encrypted_media/*.enc'
    },
    {
        'id': 'A03',
        'category': 'A03:2021 – Injection',
        'vulnerable': "Raw SQL concatenation: query string formatted with f-strings (WHERE username LIKE '%{q}%').",
        'protected': 'Parameterized SQLite queries: all user input bound safely via cursor.execute(sql, (params,)).',
        'target_endpoint': '/admin/search'
    },
    {
        'id': 'A04',
        'category': 'A04:2021 – Insecure Design',
        'vulnerable': 'No server-side file cap or type inspection; allows malicious executable payload uploads.',
        'protected': 'Defensive architecture: 50MB strict file cap, magic byte header sniffing (JPEG/PNG/MP4/MOV).',
        'target_endpoint': '/media/upload'
    },
    {
        'id': 'A05',
        'category': 'A05:2021 – Security Misconfiguration',
        'vulnerable': 'Verbose server tracebacks exposing file system paths, environment secrets, and stack traces.',
        'protected': 'Hardened production headers (CSP, X-Frame-Options: DENY, HSTS, nosniff) and generic error handlers.',
        'target_endpoint': 'Security Headers & 500 Handler'
    },
    {
        'id': 'A06',
        'category': 'A06:2021 – Vulnerable and Outdated Components',
        'vulnerable': 'Unmonitored third-party dependencies with known Common Vulnerabilities and Exposures (CVEs).',
        'protected': 'Automated pip-audit security vulnerability scanning integrated into continuous verification pipeline.',
        'target_endpoint': 'pip-audit Dependency Scan'
    },
    {
        'id': 'A07',
        'category': 'A07:2021 – Identification and Authentication Failures',
        'vulnerable': 'Unlimited brute-force login attempts permitted; single-factor authentication only.',
        'protected': 'Argon2id password hashing + mandatory RFC 6238 TOTP 2FA + 5-attempt account lockout.',
        'target_endpoint': '/auth/login & /auth/setup-2fa'
    },
    {
        'id': 'A08',
        'category': 'A08:2021 – Software and Data Integrity Failures',
        'vulnerable': 'Silent tampering acceptance: modified files or corrupted manifest records accepted without validation.',
        'protected': 'Cryptographic dual-check: Streamed SHA-256 byte comparison + 2048-bit RSA-PSS digital signatures.',
        'target_endpoint': '/verify'
    }
]

@admin_bp.route('', methods=['GET'])
@admin_bp.route('/', methods=['GET'])
@login_required
@require_role('Admin')
def dashboard():
    """
    Administration Control Center.
    Displays registered user accounts, lockout states, system metrics, and SECURE_MODE.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT user_id, username, email, role, is_locked, failed_login_attempts, created_at
        FROM users
        ORDER BY user_id ASC
        """
    )
    users = [dict(row) for row in cursor.fetchall()]

    locked_count = sum(1 for u in users if u['is_locked'])
    
    cursor.execute("SELECT COUNT(*) as total_media FROM media")
    total_media = cursor.fetchone()['total_media']

    secure_mode = current_app.config.get('SECURE_MODE', True)

    if _wants_json():
        return jsonify({
            'success': True,
            'total_users': len(users),
            'locked_users': locked_count,
            'total_media': total_media,
            'secure_mode': secure_mode,
            'users': users
        }), 200

    return render_template(
        'admin/dashboard.html',
        users=users,
        total_users=len(users),
        locked_count=locked_count,
        total_media=total_media,
        secure_mode=secure_mode
    )

@admin_bp.route('/search', methods=['GET'])
@login_required
@require_role('Admin')
def search_users():
    """
    OWASP A03 Injection Demonstrator:
    - In SECURE_MODE=True: Parameterized search safely matches literal pattern.
    - In SECURE_MODE=False: Raw string formatting permits SQL injection (e.g. ' OR '1'='1).
    """
    q = request.args.get('q', '').strip()
    db = get_db()
    cursor = db.cursor()

    secure_mode = current_app.config.get('SECURE_MODE', True)

    if secure_mode:
        # PROTECTED: Parameterized query prevents SQL injection
        cursor.execute(
            """
            SELECT user_id, username, email, role, is_locked, failed_login_attempts
            FROM users
            WHERE username LIKE ? OR email LIKE ?
            """,
            (f"%{q}%", f"%{q}%")
        )
    else:
        # VULNERABLE: Raw SQL string formatting demonstrates SQL Injection
        raw_sql = f"SELECT user_id, username, email, role, is_locked, failed_login_attempts FROM users WHERE username LIKE '%{q}%' OR email LIKE '%{q}%'"
        cursor.execute(raw_sql)

    users = [dict(row) for row in cursor.fetchall()]

    if _wants_json():
        return jsonify({
            'success': True,
            'secure_mode': secure_mode,
            'query': q,
            'count': len(users),
            'users': users
        }), 200

    return render_template(
        'admin/dashboard.html',
        users=users,
        total_users=len(users),
        locked_count=sum(1 for u in users if u['is_locked']),
        total_media=0,
        secure_mode=secure_mode,
        query=q
    )

@admin_bp.route('/unlock/<int:user_id>', methods=['POST'])
@login_required
@require_role('Admin')
def unlock_user(user_id):
    """
    Unlocks a locked user account by resetting is_locked=0 and failed_login_attempts=0.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET is_locked = 0, failed_login_attempts = 0 WHERE user_id = ?",
        (user_id,)
    )
    db.commit()

    append_audit_log(
        db,
        user_id=session.get('user_id') if 'session' in globals() else None,
        action="ACCOUNT_UNLOCK",
        details=f"Admin unlocked user account #{user_id}",
        ip_address=request.remote_addr
    )

    if _wants_json():
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': f"User account #{user_id} unlocked successfully."
        }), 200

    flash(f"User account #{user_id} unlocked successfully.", 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/secure-mode', methods=['GET'])
@login_required
@require_role('Admin')
def secure_mode_page():
    """
    Interactive SECURE_MODE Control Panel & OWASP Top 10 Comparative Matrix.
    Built for academic evaluation and live viva demonstrations with Ms. Hirra Anwar.
    """
    secure_mode = current_app.config.get('SECURE_MODE', True)

    if _wants_json():
        return jsonify({
            'success': True,
            'secure_mode': secure_mode,
            'defenses': OWASP_DEFENSES
        }), 200

    return render_template(
        'admin/secure_mode.html',
        secure_mode=secure_mode,
        defenses=OWASP_DEFENSES
    )

@admin_bp.route('/secure-mode/toggle', methods=['POST'])
@login_required
@require_role('Admin')
def toggle_secure_mode():
    """
    Toggles runtime SECURE_MODE between True (Protected) and False (Vulnerable).
    """
    new_state = not current_app.config.get('SECURE_MODE', True)
    current_app.config['SECURE_MODE'] = new_state
    Config.SECURE_MODE = new_state

    db = get_db()
    from flask import session
    append_audit_log(
        db,
        user_id=session.get('user_id'),
        action="SECURE_MODE_TOGGLE",
        details=f"SECURE_MODE toggled to {'ON (Protected)' if new_state else 'OFF (Vulnerable Viva Mode)'}",
        ip_address=request.remote_addr
    )

    if _wants_json():
        return jsonify({
            'success': True,
            'secure_mode': new_state,
            'message': f"SECURE_MODE toggled to {'ON (Protected)' if new_state else 'OFF (Vulnerable)'}"
        }), 200

    flash(
        f"SECURE_MODE is now {'ENABLED (Protected Mode)' if new_state else 'DISABLED (Vulnerable Demonstration Mode)'}",
        'info' if new_state else 'warning'
    )
    return redirect(url_for('admin.secure_mode_page'))
