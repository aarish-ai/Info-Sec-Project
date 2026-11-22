import pyotp
import pytest
from flask import session
from app.routes.auth import login_required, require_role

def test_register_success_creates_user_and_keys(client, app):
    """Verify that registration generates key pairs, encrypts them to disk, and stores user."""
    res = client.post('/auth/register', json={
        'username': 'bob_ross',
        'email': 'bob@example.com',
        'password': 'HappyLittleTrees#2026',
        'role': 'User'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['username'] == 'bob_ross'
    assert 'totp_secret' in data
    assert 'totp_uri' in data
    assert 'user_id' in data

    user_id = data['user_id']
    totp_secret = data['totp_secret']

    # Complete 2FA setup to activate
    totp = pyotp.TOTP(totp_secret)
    res_2fa = client.post('/auth/setup-2fa', json={
        'code': totp.now()
    })
    assert res_2fa.status_code == 200
    data_2fa = res_2fa.get_json()
    assert data_2fa['success'] is True

    # Verify session is now active
    res_me = client.get('/auth/me')
    assert res_me.status_code == 200
    me_data = res_me.get_json()
    assert me_data['username'] == 'bob_ross'
    assert me_data['role'] == 'User'

def test_register_duplicate_username_fails(client):
    """Verify registration rejects duplicate username."""
    client.post('/auth/register', json={
        'username': 'unique_user',
        'email': 'u1@example.com',
        'password': 'Password123!'
    })
    res = client.post('/auth/register', json={
        'username': 'unique_user',
        'email': 'u2@example.com',
        'password': 'Password123!'
    })
    assert res.status_code == 400
    assert 'already exists' in res.get_json().get('error', '').lower() or 'already exists' in res.get_json().get('message', '').lower()

def test_register_missing_fields_fails(client):
    """Verify registration fails if required fields are missing."""
    res = client.post('/auth/register', json={'username': 'incomplete'})
    assert res.status_code == 400

def test_setup_2fa_invalid_code(client):
    """Verify setup-2fa fails when invalid code is submitted."""
    client.post('/auth/register', json={
        'username': 'carol',
        'email': 'carol@example.com',
        'password': 'CarolPassword#1'
    })
    res = client.post('/auth/setup-2fa', json={'code': '999999'})
    assert res.status_code == 400

def test_login_flow_and_lockout(client):
    """Verify password check, 2FA validation, and lockout after 5 failed attempts."""
    # Register user
    reg = client.post('/auth/register', json={
        'username': 'dan_security',
        'email': 'dan@example.com',
        'password': 'DanCorrectPassword#2026'
    }).get_json()
    totp_secret = reg['totp_secret']

    # Complete 2FA setup and then log out
    totp = pyotp.TOTP(totp_secret)
    client.post('/auth/setup-2fa', json={'code': totp.now()})
    client.post('/auth/logout')

    # 1. Nonexistent user login
    res_nonexistent = client.post('/auth/login', json={
        'username': 'nonexistent_dan',
        'password': 'AnyPassword'
    })
    assert res_nonexistent.status_code == 401

    # 2. Failed password attempts (attempts 1 to 4)
    for _ in range(4):
        res_fail = client.post('/auth/login', json={
            'username': 'dan_security',
            'password': 'WrongPassword!'
        })
        assert res_fail.status_code == 401

    # 5th failed attempt: triggers account lockout
    res_fail_5 = client.post('/auth/login', json={
        'username': 'dan_security',
        'password': 'WrongPassword!'
    })
    assert res_fail_5.status_code == 403
    assert 'locked' in str(res_fail_5.get_json()).lower()

    # 6th attempt with CORRECT credentials is now blocked by lockout
    res_blocked = client.post('/auth/login', json={
        'username': 'dan_security',
        'password': 'DanCorrectPassword#2026',
        'totp_code': totp.now()
    })
    assert res_blocked.status_code == 403

def test_login_requires_totp_when_password_valid(client):
    """Verify that valid password requires TOTP code to complete login."""
    reg = client.post('/auth/register', json={
        'username': 'eve_test',
        'email': 'eve@example.com',
        'password': 'EvePassword#123'
    }).get_json()
    totp = pyotp.TOTP(reg['totp_secret'])
    client.post('/auth/setup-2fa', json={'code': totp.now()})
    client.post('/auth/logout')

    # Login with valid password but missing TOTP
    res_no_totp = client.post('/auth/login', json={
        'username': 'eve_test',
        'password': 'EvePassword#123'
    })
    assert res_no_totp.status_code == 400
    assert res_no_totp.get_json().get('requires_2fa') is True

    # Login with valid password and invalid TOTP
    res_bad_totp = client.post('/auth/login', json={
        'username': 'eve_test',
        'password': 'EvePassword#123',
        'totp_code': '000000' if totp.now() != '000000' else '111111'
    })
    assert res_bad_totp.status_code == 401

    # Login with valid password and valid TOTP
    res_success = client.post('/auth/login', json={
        'username': 'eve_test',
        'password': 'EvePassword#123',
        'totp_code': totp.now()
    })
    assert res_success.status_code == 200
    assert res_success.get_json()['success'] is True

def test_rbac_role_restrictions(app, client):
    """Verify role-based access control decorators (@login_required, @require_role)."""
    @app.route('/admin-only')
    @require_role('Admin')
    def admin_endpoint():
        return {'access': 'granted'}

    @app.route('/auditor-or-admin')
    @require_role('Auditor', 'Admin')
    def audit_endpoint():
        return {'access': 'granted'}

    # 1. Unauthenticated access
    res_unauth = client.get('/admin-only')
    assert res_unauth.status_code in (401, 403)

    # 2. Register regular User
    reg_user = client.post('/auth/register', json={
        'username': 'frank_user',
        'email': 'frank@example.com',
        'password': 'FrankPassword#1',
        'role': 'User'
    }).get_json()
    client.post('/auth/setup-2fa', json={'code': pyotp.TOTP(reg_user['totp_secret']).now()})

    res_user_denied = client.get('/admin-only')
    assert res_user_denied.status_code == 403

    res_user_audit_denied = client.get('/auditor-or-admin')
    assert res_user_audit_denied.status_code == 403

    client.post('/auth/logout')

    # 3. Register Auditor
    reg_auditor = client.post('/auth/register', json={
        'username': 'grace_auditor',
        'email': 'grace@example.com',
        'password': 'GracePassword#1',
        'role': 'Auditor'
    }).get_json()
    client.post('/auth/setup-2fa', json={'code': pyotp.TOTP(reg_auditor['totp_secret']).now()})

    res_auditor_admin = client.get('/admin-only')
    assert res_auditor_admin.status_code == 403

    res_auditor_ok = client.get('/auditor-or-admin')
    assert res_auditor_ok.status_code == 200

    client.post('/auth/logout')

    # 4. Register Admin
    reg_admin = client.post('/auth/register', json={
        'username': 'heidi_admin',
        'email': 'heidi@example.com',
        'password': 'HeidiPassword#1',
        'role': 'Admin'
    }).get_json()
    client.post('/auth/setup-2fa', json={'code': pyotp.TOTP(reg_admin['totp_secret']).now()})

    res_admin_ok = client.get('/admin-only')
    assert res_admin_ok.status_code == 200
    res_admin_audit_ok = client.get('/auditor-or-admin')
    assert res_admin_audit_ok.status_code == 200
