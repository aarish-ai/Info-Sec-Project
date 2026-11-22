from functools import wraps
from pathlib import Path
from flask import Blueprint, request, jsonify, session, current_app, redirect, url_for, Response, render_template, flash
from app.database.db import get_db
from app.core.auth_manager import (
    hash_password,
    verify_password,
    check_account_lockout,
    record_failed_attempt,
    reset_failed_attempts,
)
from app.core.totp_manager import (
    generate_totp_secret,
    get_totp_uri,
    generate_totp_qr_png,
    verify_totp_code,
)
from app.core.key_management import (
    generate_salt,
    generate_user_key_pairs,
    derive_kek,
    encrypt_private_key,
    save_encrypted_key_file,
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(f):
    """
    Decorator enforcing that an active authenticated session exists.
    Returns 401 JSON for API/JSON requests or redirects to /auth/login for browser requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            if (
                request.is_json
                or request.path.startswith('/api/')
                or 'application/json' in request.headers.get('Accept', '')
            ):
                return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_role(*roles):
    """
    Role-Based Access Control (RBAC) decorator.
    Verifies that the logged-in user holds one of the authorized roles.
    Returns 401 if unauthenticated, 403 if role unauthorized.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

            user_role = session.get('role')
            if user_role not in roles:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Access restricted to roles: {list(roles)}'
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def _wants_json():
    """Determine whether the request expects a JSON API response."""
    return (
        request.is_json
        or request.path.startswith('/api/')
        or 'application/json' in request.headers.get('Accept', '')
    )

def _get_request_data():
    """Extract parameters safely from JSON or form submissions."""
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registers a new user account.
    Generates dual RSA key pairs (signing + encryption), derives scrypt KEK,
    encrypts private keys to storage, creates unactivated user, and generates TOTP secret.
    """
    if request.method == 'GET':
        if _wants_json():
            return jsonify({'message': 'Submit registration credentials via POST'}), 200
        return render_template('auth/register.html')

    data = _get_request_data()
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = (data.get('role') or 'User').strip()

    if not username or not email or not password:
        if _wants_json():
            return jsonify({'error': 'Missing required fields: username, email, and password are required'}), 400
        flash('Missing required fields: username, email, and password are required', 'danger')
        return render_template('auth/register.html', username=username, email=email, role=role), 400

    if role not in ('User', 'Auditor', 'Admin'):
        if _wants_json():
            return jsonify({'error': f"Invalid role '{role}'. Allowed roles: User, Auditor, Admin"}), 400
        flash(f"Invalid role '{role}'. Allowed roles: User, Auditor, Admin", 'danger')
        return render_template('auth/register.html', username=username, email=email, role=role), 400

    db = get_db()
    cursor = db.cursor()

    # Check for duplicate username or email
    cursor.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", (username, email))
    if cursor.fetchone():
        if _wants_json():
            return jsonify({'error': 'Username or email already exists'}), 400
        flash('Username or email already exists', 'danger')
        return render_template('auth/register.html', username=username, email=email, role=role), 400

    # 1. Cryptographic Setup
    salt = generate_salt(16)
    pwd_hash = hash_password(password)
    keys = generate_user_key_pairs(key_size=2048)
    kek = derive_kek(password, salt)

    # 2. Encrypt private keys at rest with AES-256-GCM
    sign_ct, sign_nonce, sign_tag = encrypt_private_key(keys['signing_private_pem'], kek)
    enc_ct, enc_nonce, enc_tag = encrypt_private_key(keys['encryption_private_pem'], kek)

    # 3. Generate TOTP Multi-Factor Authentication Secret
    totp_secret = generate_totp_secret()

    # 4. Insert initial user record
    cursor.execute(
        """
        INSERT INTO users (
            username, email, password_hash, totp_secret, role,
            public_signing_key, public_encryption_key,
            encrypted_signing_key_path, encrypted_encryption_key_path,
            kdf_salt, is_locked, failed_login_attempts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
        """,
        (
            username,
            email,
            pwd_hash,
            totp_secret,
            role,
            keys['signing_public_pem'].decode('utf-8'),
            keys['encryption_public_pem'].decode('utf-8'),
            "", "",  # File paths updated below
            salt,
        )
    )
    user_id = cursor.lastrowid

    # 5. Save encrypted key files to protected storage
    key_dir = Path(current_app.config['KEY_STORAGE_DIR']) / str(user_id)
    key_dir.mkdir(parents=True, exist_ok=True)
    sign_path = key_dir / 'signing_key.enc'
    enc_path = key_dir / 'encryption_key.enc'

    save_encrypted_key_file(sign_path, sign_ct, sign_nonce, sign_tag)
    save_encrypted_key_file(enc_path, enc_ct, enc_nonce, enc_tag)

    # 6. Update user record with paths
    cursor.execute(
        """
        UPDATE users
        SET encrypted_signing_key_path = ?, encrypted_encryption_key_path = ?
        WHERE user_id = ?
        """,
        (str(sign_path), str(enc_path), user_id)
    )
    db.commit()

    # 7. Store pending registration in session for 2FA verification step
    session['pending_user_id'] = user_id
    session['pending_totp_secret'] = totp_secret
    session['pending_kek'] = kek.hex()

    totp_uri = get_totp_uri(username, totp_secret)

    if _wants_json():
        return jsonify({
            'success': True,
            'message': 'Registration successful. Complete 2FA setup to activate account.',
            'user_id': user_id,
            'username': username,
            'totp_secret': totp_secret,
            'totp_uri': totp_uri,
        }), 201

    flash('Registration successful! Please scan the QR code to set up 2FA.', 'success')
    return redirect(url_for('auth.setup_2fa'))

@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
def setup_2fa():
    """
    Verifies initial TOTP code to confirm authenticator setup and activate session.
    """
    if request.method == 'GET':
        if _wants_json():
            return jsonify({'message': 'Submit 2FA verification code via POST'}), 200
        totp_secret = session.get('pending_totp_secret', '')
        return render_template('auth/setup_2fa.html', totp_secret=totp_secret)

    data = _get_request_data()
    code = (data.get('code') or '').strip()
    if not code:
        if _wants_json():
            return jsonify({'error': '2FA verification code is required'}), 400
        flash('2FA verification code is required', 'danger')
        return render_template('auth/setup_2fa.html', totp_secret=session.get('pending_totp_secret', '')), 400

    user_id = data.get('user_id') or session.get('pending_user_id') or session.get('user_id')
    if not user_id:
        if _wants_json():
            return jsonify({'error': 'No pending user registration or session found'}), 400
        flash('No pending user registration or session found', 'danger')
        return redirect(url_for('auth.register'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, username, role, totp_secret FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        if _wants_json():
            return jsonify({'error': 'User not found'}), 404
        flash('User not found', 'danger')
        return redirect(url_for('auth.register'))

    totp_secret = session.get('pending_totp_secret') or user['totp_secret']

    if not verify_totp_code(totp_secret, code):
        if _wants_json():
            return jsonify({'error': 'Invalid 2FA code'}), 400
        flash('Invalid 2FA code. Please check your authenticator and try again.', 'danger')
        return render_template('auth/setup_2fa.html', totp_secret=totp_secret), 400

    # Activation confirmed: establish logged-in session
    session.pop('pending_user_id', None)
    session.pop('pending_totp_secret', None)
    pending_kek = session.pop('pending_kek', None)

    session['user_id'] = user['user_id']
    session['username'] = user['username']
    session['role'] = user['role']
    if pending_kek:
        session['kek'] = pending_kek

    if _wants_json():
        return jsonify({
            'success': True,
            'message': '2FA verified and account activated',
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user['role']
        }), 200

    flash('Account successfully activated!', 'success')
    return redirect(url_for('general.index'))

@auth_bp.route('/totp-qr', methods=['GET'])
def totp_qr():
    """Streams the QR code PNG image for the active or pending TOTP registration."""
    user_id = session.get('pending_user_id') or session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No active session or pending registration'}), 401

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username, totp_secret FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'User not found'}), 404

    uri = get_totp_uri(row['username'], row['totp_secret'])
    qr_png = generate_totp_qr_png(uri)
    return Response(qr_png, mimetype='image/png')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Authenticates a user via password (Argon2id) and TOTP code.
    Enforces account lockout (5 failed attempts) and stores KEK in session upon success.
    """
    if request.method == 'GET':
        if _wants_json():
            return jsonify({'message': 'Submit login credentials via POST'}), 200
        return render_template('auth/login.html')

    data = _get_request_data()
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    totp_code = (data.get('totp_code') or data.get('code') or '').strip()

    if not username or not password:
        if _wants_json():
            return jsonify({'error': 'Username and password are required'}), 400
        flash('Username and password are required', 'danger')
        return render_template('auth/login.html', username=username), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT user_id, username, password_hash, totp_secret, role, kdf_salt, is_locked, failed_login_attempts
        FROM users WHERE username = ?
        """,
        (username,)
    )
    user = cursor.fetchone()

    if not user:
        if _wants_json():
            return jsonify({'error': 'Invalid credentials'}), 401
        flash('Invalid credentials', 'danger')
        return render_template('auth/login.html', username=username), 401

    user_id = user['user_id']

    # 1. Lockout Check
    if check_account_lockout(db, user_id):
        if _wants_json():
            return jsonify({'error': 'Account is locked due to too many failed login attempts. Contact an administrator.'}), 403
        flash('Account is locked due to too many failed login attempts. Contact an administrator.', 'danger')
        return render_template('auth/login.html', username=username, is_locked=True), 403

    # 2. Password Verification (Argon2id)
    if not verify_password(user['password_hash'], password):
        attempts = record_failed_attempt(db, user_id)
        if attempts >= 5:
            if _wants_json():
                return jsonify({'error': 'Account is locked due to too many failed login attempts.'}), 403
            flash('Account is locked due to too many failed login attempts.', 'danger')
            return render_template('auth/login.html', username=username, is_locked=True, failed_attempts=attempts), 403
        if _wants_json():
            return jsonify({'error': 'Invalid credentials'}), 401
        flash('Invalid credentials', 'danger')
        return render_template('auth/login.html', username=username, failed_attempts=attempts), 401

    # 3. Two-Factor Authentication Check
    if not totp_code:
        if _wants_json():
            return jsonify({
                'error': '2FA code required',
                'requires_2fa': True,
                'message': 'Password correct; please provide your 6-digit TOTP code.'
            }), 400
        flash('Password verified; please enter your 6-digit TOTP authenticator code.', 'info')
        return render_template('auth/login.html', username=username), 400

    if not verify_totp_code(user['totp_secret'], totp_code):
        attempts = record_failed_attempt(db, user_id)
        if attempts >= 5:
            if _wants_json():
                return jsonify({'error': 'Account is locked due to too many failed login attempts.'}), 403
            flash('Account is locked due to too many failed login attempts.', 'danger')
            return render_template('auth/login.html', username=username, is_locked=True, failed_attempts=attempts), 403
        if _wants_json():
            return jsonify({'error': 'Invalid 2FA code'}), 401
        flash('Invalid 2FA code', 'danger')
        return render_template('auth/login.html', username=username, failed_attempts=attempts), 401

    # 4. Successful Authentication
    reset_failed_attempts(db, user_id)
    kek = derive_kek(password, user['kdf_salt'])

    session.clear()
    session['user_id'] = user_id
    session['username'] = user['username']
    session['role'] = user['role']
    session['kek'] = kek.hex()

    if _wants_json():
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'user_id': user_id,
                'username': user['username'],
                'role': user['role']
            }
        }), 200

    flash(f"Welcome back, {user['username']}!", 'success')
    return redirect(url_for('general.index'))

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Clears user session and logs out."""
    session.clear()
    if request.method == 'GET' and not _wants_json():
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('auth.login'))
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    """Returns currently authenticated user profile information."""
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username'],
        'role': session['role'],
        'authenticated': True
    }), 200
