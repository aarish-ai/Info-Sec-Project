import pyotp
import pytest
from app.core.audit_chain import append_audit_log
from app.database.db import get_db

def _register_and_login(client, username, role="User"):
    res = client.post('/auth/register', json={
        'username': username,
        'email': f'{username}@example.com',
        'password': 'StrongPassword#2026',
        'role': role
    })
    data = res.get_json()
    totp = pyotp.TOTP(data['totp_secret'])
    client.post('/auth/setup-2fa', json={'code': totp.now()})
    return data['user_id']

def test_audit_route_unauthenticated_blocked(client):
    """Unauthenticated access to /audit is blocked with 401 or redirect to login."""
    res = client.get('/audit', headers={'Accept': 'application/json'})
    assert res.status_code == 401

    res_html = client.get('/audit')
    assert res_html.status_code in (302, 401)

def test_audit_route_regular_user_forbidden(client):
    """Users with 'User' role are rejected with 403 Forbidden."""
    _register_and_login(client, "regular_user", role="User")
    res = client.get('/audit', headers={'Accept': 'application/json'})
    assert res.status_code == 403

    res_html = client.get('/audit')
    assert res_html.status_code == 403

def test_audit_route_auditor_access(client, app):
    """Users with 'Auditor' role have full access to view audit log and verify chain."""
    auditor_id = _register_and_login(client, "auditor_user", role="Auditor")

    with app.app_context():
        db = get_db()
        append_audit_log(db, user_id=auditor_id, action="LOGIN", details="Auditor session started", ip_address="127.0.0.1")
        append_audit_log(db, user_id=auditor_id, action="VERIFY", details="Verified media asset", ip_address="127.0.0.1")

    # HTML access
    res = client.get('/audit')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Cryptographic Audit Trail' in html
    assert 'Verify Entire Audit Chain' in html
    assert 'Auditor session started' in html
    assert 'table-vault' in html

    # JSON access
    res_json = client.get('/audit', headers={'Accept': 'application/json'})
    assert res_json.status_code == 200
    data = res_json.get_json()
    assert data['success'] is True
    assert data['count'] >= 2
    assert len(data['logs']) >= 2

def test_audit_route_admin_access(client, app):
    """Admin role can also access the audit log."""
    _register_and_login(client, "admin_auditor", role="Admin")
    res = client.get('/audit')
    assert res.status_code == 200

def test_verify_chain_endpoint_intact(client, app):
    """POST /audit/verify-chain returns valid status when chain is uncorrupted."""
    auditor_id = _register_and_login(client, "verifier_auditor", role="Auditor")
    with app.app_context():
        db = get_db()
        append_audit_log(db, user_id=auditor_id, action="ACTION_1", details="First test log", ip_address="127.0.0.1")
        append_audit_log(db, user_id=auditor_id, action="ACTION_2", details="Second test log", ip_address="127.0.0.1")

    res = client.post('/audit/verify-chain', headers={'Accept': 'application/json'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['valid'] is True
    assert data['corrupted_log_id'] == 0
    assert "intact" in data['message'].lower()

def test_verify_chain_endpoint_tampered(client, app):
    """POST /audit/verify-chain detects tampered database row and returns corrupted log ID."""
    auditor_id = _register_and_login(client, "tamper_detector", role="Auditor")
    with app.app_context():
        db = get_db()
        id1 = append_audit_log(db, user_id=auditor_id, action="ACTION_A", details="Genuine log A", ip_address="127.0.0.1")
        id2 = append_audit_log(db, user_id=auditor_id, action="ACTION_B", details="Genuine log B", ip_address="127.0.0.1")

        # Directly tamper the database
        cursor = db.cursor()
        cursor.execute("UPDATE audit_log SET details = 'MALICIOUS_TAMPER' WHERE log_id = ?", (id2,))
        db.commit()

    res = client.post('/audit/verify-chain', headers={'Accept': 'application/json'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['valid'] is False
    assert data['corrupted_log_id'] == id2
    assert "broken" in data['message'].lower()

def test_audit_log_search_filter(client, app):
    """GET /audit?q=... filters rows matching the query string."""
    auditor_id = _register_and_login(client, "search_auditor", role="Auditor")
    with app.app_context():
        db = get_db()
        append_audit_log(db, user_id=auditor_id, action="SPECIAL_ACTION", details="Unique token 778899", ip_address="127.0.0.1")
        append_audit_log(db, user_id=auditor_id, action="OTHER_ACTION", details="Irrelevant", ip_address="127.0.0.1")

    res = client.get('/audit?q=778899', headers={'Accept': 'application/json'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['count'] == 1
    assert data['logs'][0]['action'] == "SPECIAL_ACTION"
