import io
import pyotp
import pytest
from app.database.db import get_db

def register_and_login_user(client, app, username="verifier_uploader", password="Password123!"):
    """Helper to register and 2FA authenticate a user."""
    client.post('/auth/register', json={
        'username': username,
        'email': f'{username}@example.com',
        'password': password,
        'role': 'User'
    })
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT user_id, totp_secret FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        user_id = user['user_id']
        totp_secret = user['totp_secret']

    totp = pyotp.TOTP(totp_secret)
    client.post('/auth/setup-2fa', json={
        'user_id': user_id,
        'code': totp.now()
    })
    return user_id

def test_verify_page_renders_with_optional_cert_id(client):
    """GET /verify renders the public verification form and pre-fills cert_id if provided."""
    res = client.get('/verify?cert_id=test-uuid-1234')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Public Verification Portal' in html
    assert 'test-uuid-1234' in html

def test_verify_unknown_outcome(client):
    """POST /verify with nonexistent cert_id returns UNKNOWN verdict."""
    fake_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'UNKNOWN_TEST'
    data = {
        'cert_id': '00000000-0000-0000-0000-000000000000',
        'file': (io.BytesIO(fake_png), 'test.png')
    }
    res = client.post('/verify', data=data, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    assert res.status_code in (200, 404)
    json_data = res.get_json()
    assert json_data['verdict'] == 'UNKNOWN'

def test_verify_authentic_outcome(client, app):
    """POST /verify with identical file and valid signature yields AUTHENTIC verdict."""
    register_and_login_user(client, app, "alice_original")

    # Upload genuine image
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'AUTHENTIC_ASSET_CONTENT' * 10
    upload_res = client.post('/media/upload', data={'file': (io.BytesIO(png_data), 'contract.png')}, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    assert upload_res.status_code == 201
    media_id = upload_res.get_json()['media_id']

    # Unauthenticated guest verifies the file
    client.get('/auth/logout')

    verify_data = {
        'cert_id': media_id,
        'file': (io.BytesIO(png_data), 'submitted_contract.png')
    }
    verify_res = client.post('/verify', data=verify_data, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    assert verify_res.status_code == 200
    res_json = verify_res.get_json()
    assert res_json['verdict'] == 'AUTHENTIC'
    assert res_json['hash_match'] is True
    assert res_json['signature_valid'] is True

    # Check verification history database record
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM verification_history WHERE media_id = ?", (media_id,))
        record = cursor.fetchone()
        assert record is not None
        assert record['overall_status'] == 'AUTHENTIC'
        assert record['hash_match'] == 1
        assert record['signature_valid'] == 1

def test_verify_modified_outcome(client, app):
    """POST /verify with altered content but valid manifest signature yields MODIFIED verdict."""
    register_and_login_user(client, app, "bob_original")

    original_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'ORIGINAL_EVIDENCE' * 10
    upload_res = client.post('/media/upload', data={'file': (io.BytesIO(original_png), 'evidence.png')}, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    media_id = upload_res.get_json()['media_id']

    client.get('/auth/logout')

    # Altered file: header is still PNG, but content has been modified/tampered
    tampered_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'TAMPERED_MODIFIED_DATA' * 10
    verify_data = {
        'cert_id': media_id,
        'file': (io.BytesIO(tampered_png), 'evidence.png')
    }
    verify_res = client.post('/verify', data=verify_data, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    assert verify_res.status_code == 200
    res_json = verify_res.get_json()
    assert res_json['verdict'] == 'MODIFIED'
    assert res_json['hash_match'] is False
    assert res_json['signature_valid'] is True
    assert 'phash_distance' in res_json

    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM verification_history WHERE media_id = ? ORDER BY verification_id DESC", (media_id,))
        record = cursor.fetchone()
        assert record is not None
        assert record['overall_status'] == 'MODIFIED'
        assert record['hash_match'] == 0
        assert record['signature_valid'] == 1

def test_verify_invalid_signature_outcome(client, app):
    """POST /verify when digital signature is corrupted or forged yields INVALID_SIGNATURE verdict."""
    register_and_login_user(client, app, "charlie_original")

    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'FORGERY_TEST' * 10
    upload_res = client.post('/media/upload', data={'file': (io.BytesIO(png_data), 'signed_doc.png')}, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    media_id = upload_res.get_json()['media_id']

    # Corrupt digital signature directly in database (simulating database tampering)
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE media SET digital_signature = ? WHERE media_id = ?", (b'FORGED_SIGNATURE_BYTES_1234', media_id))
        db.commit()

    client.get('/auth/logout')

    verify_data = {
        'cert_id': media_id,
        'file': (io.BytesIO(png_data), 'signed_doc.png')
    }
    verify_res = client.post('/verify', data=verify_data, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    assert verify_res.status_code == 200
    res_json = verify_res.get_json()
    assert res_json['verdict'] == 'INVALID_SIGNATURE'
    assert res_json['signature_valid'] is False
