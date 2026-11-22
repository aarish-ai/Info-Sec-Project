import io
import os
import pyotp
import pytest
from pathlib import Path
from app.database.db import get_db

def register_and_login_user(client, app, username="testuser", password="Password123!", role="User"):
    """Helper to register and 2FA authenticate a user, returning user_id."""
    res = client.post('/auth/register', json={
        'username': username,
        'email': f'{username}@example.com',
        'password': password,
        'role': role
    })
    assert res.status_code == 201

    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT user_id, totp_secret FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        user_id = user['user_id']
        totp_secret = user['totp_secret']

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    res_2fa = client.post('/auth/setup-2fa', json={
        'user_id': user_id,
        'code': code
    })
    assert res_2fa.status_code == 200
    return user_id

def test_unauthenticated_access_redirects(client):
    """Accessing /media routes without session redirects to login or returns 401."""
    res = client.get('/media')
    assert res.status_code in (302, 401)
    if res.status_code == 302:
        assert '/auth/login' in res.headers['Location']

def test_media_upload_and_zero_plaintext_pipeline(client, app):
    """Test full upload pipeline: envelope encryption, zero-plaintext storage, and record creation."""
    user_id = register_and_login_user(client, app, "alice_uploader")

    # Genuine PNG payload
    png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    fake_png_body = b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89' + b'PNG_PAYLOAD_SECRET_DATA'
    sample_file_data = png_header + fake_png_body

    data = {
        'file': (io.BytesIO(sample_file_data), 'evidence_01.png')
    }

    res = client.post('/media/upload', data=data, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data['success'] is True
    media_id = json_data['media_id']

    # Verify database entry
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM media WHERE media_id = ?", (media_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row['original_filename'] == 'evidence_01.png'
        assert row['file_type'] == 'image/png'
        assert row['owner_id'] == user_id
        assert len(row['wrapped_aes_key']) > 0
        assert len(row['nonce']) == 12
        assert len(row['auth_tag']) == 16
        assert len(row['digital_signature']) > 0

        # Verify ciphertext on disk
        enc_path = Path(row['encrypted_file_path'])
        assert enc_path.exists()
        ciphertext = enc_path.read_bytes()
        # Plaintext must NOT appear in ciphertext
        assert b'PNG_PAYLOAD_SECRET_DATA' not in ciphertext

def test_media_upload_invalid_file_rejected(client, app):
    """Uploading a file with spoofed extension must return 400 error."""
    register_and_login_user(client, app, "bob_uploader")

    spoofed_file = (io.BytesIO(b'plain text pretending to be png'), 'fake.png')
    res = client.post('/media/upload', data={'file': spoofed_file}, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    assert res.status_code == 400
    json_data = res.get_json()
    assert 'error' in json_data

def test_media_download_and_idor_protection(client, app):
    """User A downloads decrypted media; User B attempting download gets 403 Forbidden."""
    user_a_id = register_and_login_user(client, app, "user_alpha")

    # Upload test image
    jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00' + b'SENSITIVE_INVESTIGATION_PHOTO'
    data = {'file': (io.BytesIO(jpeg_data), 'alpha_doc.jpg')}
    upload_res = client.post('/media/upload', data=data, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    assert upload_res.status_code == 201
    media_id = upload_res.get_json()['media_id']

    # User A downloads own file
    dl_res = client.get(f'/media/{media_id}/download')
    assert dl_res.status_code == 200
    assert dl_res.data == jpeg_data
    assert 'attachment' in dl_res.headers['Content-Disposition']

    # Register and log in User B
    client.get('/auth/logout')  # clear session
    user_b_id = register_and_login_user(client, app, "user_beta")

    # User B attempts to download User A's file (IDOR attack)
    idor_res = client.get(f'/media/{media_id}/download')
    assert idor_res.status_code == 403

    # User B attempts to preview User A's file
    idor_preview = client.get(f'/media/{media_id}/preview')
    assert idor_preview.status_code == 403

def test_media_certificate_generation_and_download(client, app):
    """Logged in user can download official PDF verification certificate for registered media."""
    register_and_login_user(client, app, "carol_uploader")

    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'TEST_DATA' * 10
    upload_res = client.post('/media/upload', data={'file': (io.BytesIO(png_data), 'cert_test.png')}, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    media_id = upload_res.get_json()['media_id']

    cert_res = client.get(f'/media/{media_id}/certificate')
    assert cert_res.status_code == 200
    assert cert_res.headers['Content-Type'] == 'application/pdf'
    assert 'attachment' in cert_res.headers['Content-Disposition']
    assert cert_res.data.startswith(b'%PDF-')

def test_media_preview_image_and_video_handling(client, app):
    """Image preview renders template; Video preview redirects to secure download stream."""
    register_and_login_user(client, app, "dave_uploader")

    # 1. Image preview
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + b'IMAGE_DATA' * 5
    img_res = client.post('/media/upload', data={'file': (io.BytesIO(png_data), 'photo.png')}, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    img_id = img_res.get_json()['media_id']

    prev_res = client.get(f'/media/{img_id}/preview')
    assert prev_res.status_code == 200
    html = prev_res.get_data(as_text=True)
    assert 'data:image/png;base64,' in html
    assert 'photo.png' in html

    # 2. Video preview handling
    mp4_data = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42' + b'VIDEO_DATA' * 10
    vid_res = client.post('/media/upload', data={'file': (io.BytesIO(mp4_data), 'clip.mp4')}, content_type='multipart/form-data', headers={'Accept': 'application/json'})
    vid_id = vid_res.get_json()['media_id']

    vid_prev = client.get(f'/media/{vid_id}/preview')
    # Video preview redirects to download or returns download prompt
    assert vid_prev.status_code in (302, 200)
    if vid_prev.status_code == 302:
        assert f'/media/{vid_id}/download' in vid_prev.headers['Location']
