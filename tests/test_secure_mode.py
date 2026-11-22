import io
import pyotp
import pytest
from app.database.db import get_db

def _register_and_login(client, username, role="User"):
    res = client.post('/auth/register', json={
        'username': username,
        'email': f'{username}@example.com',
        'password': 'AdminTestPassword#2026',
        'role': role
    })
    data = res.get_json()
    totp = pyotp.TOTP(data['totp_secret'])
    client.post('/auth/setup-2fa', json={'code': totp.now()})
    return data['user_id']

def test_admin_dashboard_rbac(client):
    """Verify standard users cannot access /admin, but Admin role can."""
    # 1. Unauthenticated
    res = client.get('/admin', headers={'Accept': 'application/json'})
    assert res.status_code == 401

    # 2. Regular User
    _register_and_login(client, "regular_joe", role="User")
    res_user = client.get('/admin', headers={'Accept': 'application/json'})
    assert res_user.status_code == 403

    client.post('/auth/logout')

    # 3. Admin User
    _register_and_login(client, "super_admin", role="Admin")
    res_admin = client.get('/admin')
    assert res_admin.status_code == 200
    html = res_admin.get_data(as_text=True)
    assert 'System Administration' in html
    assert 'User Accounts' in html

def test_admin_unlock_account(client, app):
    """Admin can unlock an account locked due to excessive failed logins."""
    admin_id = _register_and_login(client, "admin_unlocker", role="Admin")

    # Manually lock a user in database
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO users (
                username, email, password_hash, totp_secret, role,
                public_signing_key, public_encryption_key,
                encrypted_signing_key_path, encrypted_encryption_key_path,
                kdf_salt, is_locked, failed_login_attempts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 5)
            """,
            (
                "locked_victim", "locked@example.com", "hash", "SECRET", "User",
                "pub_s", "pub_e", "/s", "/e", b'salt123456789012'
            )
        )
        db.commit()
        victim_id = cursor.lastrowid

    # Unlock via Admin POST
    res = client.post(f'/admin/unlock/{victim_id}', headers={'Accept': 'application/json'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True

    # Verify user record is unlocked
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_locked, failed_login_attempts FROM users WHERE user_id = ?", (victim_id,))
        row = cursor.fetchone()
        assert row['is_locked'] == 0
        assert row['failed_login_attempts'] == 0

def test_secure_mode_toggle_controller(client, app):
    """Admin can toggle SECURE_MODE between True and False."""
    _register_and_login(client, "admin_toggler", role="Admin")

    assert app.config.get('SECURE_MODE', True) is True

    # Toggle to False
    res_toggle = client.post('/admin/secure-mode/toggle', headers={'Accept': 'application/json'})
    assert res_toggle.status_code == 200
    data = res_toggle.get_json()
    assert data['secure_mode'] is False
    assert app.config['SECURE_MODE'] is False

    # Toggle back to True
    res_toggle_2 = client.post('/admin/secure-mode/toggle', headers={'Accept': 'application/json'})
    assert res_toggle_2.status_code == 200
    assert res_toggle_2.get_json()['secure_mode'] is True
    assert app.config['SECURE_MODE'] is True

def test_secure_mode_idor_dual_behavior(client, app):
    """
    Demonstrates OWASP A01 Broken Access Control:
    - When SECURE_MODE=True: User B downloading User A's file receives 403 Forbidden.
    - When SECURE_MODE=False: User B downloading User A's file bypasses ownership check and succeeds (200 OK).
    """
    # 1. User A uploads private image
    user_a_id = _register_and_login(client, "alice_idor", role="User")
    png_data = b'\x89PNG\r\n\x1a\n' + b'SENSITIVE_INVESTIGATION_DOC' * 5
    upload_res = client.post(
        '/media/upload',
        data={'file': (io.BytesIO(png_data), 'alice_private.png')},
        content_type='multipart/form-data',
        headers={'Accept': 'application/json'}
    )
    media_id = upload_res.get_json()['media_id']

    client.post('/auth/logout')

    # 2. User B logs in
    user_b_id = _register_and_login(client, "bob_attacker", role="User")

    # In SECURE_MODE = True: IDOR is strictly blocked (403)
    app.config['SECURE_MODE'] = True
    res_blocked = client.get(f'/media/{media_id}/download', headers={'Accept': 'application/json'})
    assert res_blocked.status_code == 403

    # Switch to SECURE_MODE = False (vulnerable viva mode)
    app.config['SECURE_MODE'] = False
    res_vulnerable = client.get(f'/media/{media_id}/download')
    assert res_vulnerable.status_code == 200
    assert 'attachment' in res_vulnerable.headers['Content-Disposition']

    # Restore SECURE_MODE
    app.config['SECURE_MODE'] = True

def test_secure_mode_sqli_dual_behavior(client, app):
    """
    Demonstrates OWASP A03 Injection:
    - When SECURE_MODE=True: Parameterized search treats "' OR '1'='1" literally.
    - When SECURE_MODE=False: Raw string interpolation evaluates SQL injection and returns all accounts.
    """
    _register_and_login(client, "admin_sqli", role="Admin")

    # Payload designed to force TRUE in SQL query
    sqli_payload = "' OR '1'='1"

    # In SECURE_MODE = True: Parameterized query finds 0 matches for literal payload
    app.config['SECURE_MODE'] = True
    res_safe = client.get(f'/admin/search?q={sqli_payload}', headers={'Accept': 'application/json'})
    assert res_safe.status_code == 200
    safe_data = res_safe.get_json()
    assert safe_data['count'] == 0

    # In SECURE_MODE = False: Raw string interpolation causes SQL injection
    app.config['SECURE_MODE'] = False
    res_vuln = client.get(f'/admin/search?q={sqli_payload}', headers={'Accept': 'application/json'})
    assert res_vuln.status_code == 200
    vuln_data = res_vuln.get_json()
    # SQL injection returns all accounts in the database
    assert vuln_data['count'] > 0

    app.config['SECURE_MODE'] = True

def test_admin_secure_mode_page_renders_8_owasp_cards(client):
    """Verify /admin/secure-mode displays all 8 OWASP Top 10 comparative defense cards."""
    _register_and_login(client, "admin_viewer", role="Admin")
    res = client.get('/admin/secure-mode')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'OWASP Top 10 Security Architecture Matrix' in html
    assert 'A01' in html
    assert 'A02' in html
    assert 'A03' in html
    assert 'A04' in html
    assert 'A05' in html
    assert 'A06' in html
    assert 'A07' in html
    assert 'A08' in html
    assert 'Toggle SECURE_MODE' in html
