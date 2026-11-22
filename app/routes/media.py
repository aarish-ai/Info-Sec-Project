import io
import os
import uuid
import base64
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    current_app,
    redirect,
    url_for,
    render_template,
    flash,
    send_file,
)
from werkzeug.utils import secure_filename
from app.database.db import get_db
from app.routes.auth import login_required
from app.core.validators import validate_upload
from app.core.hashing import compute_streamed_sha256, compute_phash
from app.core.signatures import build_canonical_manifest, sign_manifest
from app.core.ciphers import encrypt_media_envelope, decrypt_media_envelope
from app.core.key_management import load_encrypted_key_file
from app.core.certificate import generate_verification_certificate_pdf

media_bp = Blueprint('media', __name__, url_prefix='/media')

def _wants_json():
    """Determine whether the request expects a JSON API response."""
    return (
        request.is_json
        or request.path.startswith('/api/')
        or 'application/json' in request.headers.get('Accept', '')
    )

@media_bp.route('', methods=['GET'])
@media_bp.route('/', methods=['GET'])
@login_required
def media_library():
    """
    User Media Library / Vault.
    Displays all media assets encrypted and registered by the authenticated user.
    """
    user_id = session.get('user_id')
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT media_id, original_filename, file_type, file_size, sha256_hash, phash, registration_timestamp
        FROM media
        WHERE owner_id = ?
        ORDER BY registration_timestamp DESC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    media_list = [dict(row) for row in rows]

    if _wants_json():
        return jsonify({
            'success': True,
            'count': len(media_list),
            'media': media_list
        }), 200

    return render_template('media/library.html', media_list=media_list)

@media_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """
    Media Upload & Zero-Plaintext Encryption Pipeline.
    1. Validates magic bytes, extension, and file size cap.
    2. Computes streamed SHA-256 and perceptual pHash.
    3. Builds canonical JSON manifest and signs it with user's RSA-PSS private key.
    4. Encrypts media payload via AES-256-GCM envelope encryption.
    5. Saves encrypted ciphertext to storage and inserts provenance record.
    6. Permanently purges/closes plaintext memory buffers (Zero-Plaintext policy).
    """
    if request.method == 'GET':
        if _wants_json():
            return jsonify({'message': 'Submit multipart form with file to /media/upload'}), 200
        return render_template('media/upload.html')

    # Extract uploaded file
    file_storage = request.files.get('file') or request.files.get('media')
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)

    # 1. Validation & Magic Bytes Sniffing
    is_valid, err_msg, detected_mime = validate_upload(file_storage, max_size=max_size)
    if not is_valid:
        if _wants_json():
            return jsonify({'error': err_msg}), 400
        flash(err_msg, 'danger')
        return render_template('media/upload.html'), 400

    user_id = session.get('user_id')
    filename = secure_filename(file_storage.filename)

    # 2. Compute Hashes
    sha256_hash = compute_streamed_sha256(file_storage)
    phash = compute_phash(file_storage)

    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    media_id = str(uuid.uuid4())
    timestamp_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    # 3. Canonical Manifest
    canonical_manifest = build_canonical_manifest(
        media_id=media_id,
        owner_id=user_id,
        filename=filename,
        file_size=file_size,
        mime_type=detected_mime,
        sha256_hash=sha256_hash,
        phash=phash,
        timestamp_utc=timestamp_utc
    )

    # 4. Digital Signature via user's private signing key
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT encrypted_signing_key_path, public_encryption_key
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )
    user_record = cursor.fetchone()
    if not user_record:
        if _wants_json():
            return jsonify({'error': 'User account not found'}), 404
        flash('User account not found', 'danger')
        return redirect(url_for('auth.login'))

    kek_hex = session.get('kek')
    if not kek_hex:
        if _wants_json():
            return jsonify({'error': 'Session encryption key unavailable. Please re-authenticate.'}), 401
        flash('Session encryption key unavailable. Please log in again to unlock your keys.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        kek = bytes.fromhex(kek_hex)
        priv_sign_pem = load_encrypted_key_file(user_record['encrypted_signing_key_path'], kek)
        digital_signature = sign_manifest(canonical_manifest, priv_sign_pem)
    except Exception as e:
        if _wants_json():
            return jsonify({'error': f'Failed to sign manifest: {str(e)}'}), 500
        flash('Failed to sign media manifest. Key unwrapping failed.', 'danger')
        return redirect(url_for('media.media_library'))

    # 5. Envelope Encryption with user's RSA encryption public key
    file_storage.seek(0)
    file_bytes = file_storage.read()

    try:
        envelope = encrypt_media_envelope(file_bytes, user_record['public_encryption_key'])
    finally:
        # ZERO-PLAINTEXT POLICY: Wipe plaintext reference from memory and close stream
        del file_bytes
        try:
            file_storage.close()
        except Exception:
            pass

    # 6. Save encrypted ciphertext to storage
    enc_dir = Path(current_app.config['ENCRYPTED_MEDIA_DIR'])
    enc_dir.mkdir(parents=True, exist_ok=True)
    enc_file_path = enc_dir / f"{media_id}.enc"
    enc_file_path.write_bytes(envelope['ciphertext'])

    # 7. Record in SQLite Database
    cursor.execute(
        """
        INSERT INTO media (
            media_id, owner_id, original_filename, file_type, file_size,
            sha256_hash, phash, encrypted_file_path, wrapped_aes_key, nonce, auth_tag,
            registration_manifest, digital_signature, registration_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            media_id,
            user_id,
            filename,
            detected_mime,
            file_size,
            sha256_hash,
            phash,
            str(enc_file_path),
            envelope['wrapped_aes_key'],
            envelope['nonce'],
            envelope['auth_tag'],
            canonical_manifest,
            digital_signature,
            timestamp_utc
        )
    )

    # 8. Record in Audit Log
    try:
        from app.core.audit_chain import append_audit_log
        append_audit_log(
            user_id=user_id,
            action="MEDIA_UPLOAD",
            details=f"Registered {filename} (ID: {media_id})",
            ip_address=request.remote_addr or "127.0.0.1"
        )
    except Exception:
        # Fallback direct insert if audit_chain module not yet built
        cursor.execute("SELECT current_hash FROM audit_log ORDER BY log_id DESC LIMIT 1")
        last_log = cursor.fetchone()
        prev_h = last_log['current_hash'] if last_log else "0" * 64
        curr_h = hashlib.sha256(f"{prev_h}:{user_id}:MEDIA_UPLOAD:{media_id}".encode('utf-8')).hexdigest()
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, details, ip_address, prev_hash, current_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, "MEDIA_UPLOAD", f"Registered {filename} (ID: {media_id})", request.remote_addr or "127.0.0.1", prev_h, curr_h)
        )

    db.commit()

    if _wants_json():
        return jsonify({
            'success': True,
            'message': 'Media uploaded and encrypted successfully',
            'media_id': media_id,
            'filename': filename,
            'sha256_hash': sha256_hash,
            'phash': phash,
            'mime_type': detected_mime
        }), 201

    flash(f"Media '{filename}' successfully encrypted and registered to vault!", 'success')
    return redirect(url_for('media.media_library'))

@media_bp.route('/<media_id>/certificate', methods=['GET'])
@login_required
def download_certificate(media_id: str):
    """
    Generates and streams the official PDF Verification Certificate of Provenance
    with an embedded dynamic QR code.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT m.*, u.username as owner_username
        FROM media m
        JOIN users u ON m.owner_id = u.user_id
        WHERE m.media_id = ?
        """,
        (media_id,)
    )
    record = cursor.fetchone()
    if not record:
        if _wants_json():
            return jsonify({'error': 'Media record not found'}), 404
        flash('Media record not found', 'danger')
        return redirect(url_for('media.media_library'))

    base_url = request.host_url
    pdf_bytes = generate_verification_certificate_pdf(dict(record), base_url)

    filename = record['original_filename']
    download_name = f"MediaGuard_Certificate_{filename}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=download_name
    )

@media_bp.route('/<media_id>/download', methods=['GET'])
@login_required
def download_media(media_id: str):
    """
    Secure Decryption & Download Endpoint.
    Enforces strict IDOR protection (only the verified owner can decrypt).
    Unwraps the AES key, decrypts ciphertext, validates SHA-256 integrity,
    and streams decrypted plaintext to the client.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM media WHERE media_id = ?", (media_id,))
    record = cursor.fetchone()
    if not record:
        if _wants_json():
            return jsonify({'error': 'Media record not found'}), 404
        flash('Media record not found', 'danger')
        return redirect(url_for('media.media_library'))

    user_id = session.get('user_id')

    # Dual-Behavior IDOR Access Control Check (OWASP A01)
    if current_app.config.get('SECURE_MODE', True):
        if record['owner_id'] != user_id:
            if _wants_json():
                return jsonify({'error': 'Forbidden', 'message': 'Access denied: You do not own this media.'}), 403
            flash('Access denied: You do not own this media asset.', 'danger')
            return redirect(url_for('media.media_library')), 403
    else:
        # SECURE_MODE = False (Vulnerable Viva Demonstration Mode): Ownership check bypassed
        if record['owner_id'] != user_id:
            enc_path = Path(record['encrypted_file_path'])
            if enc_path.exists():
                return send_file(
                    enc_path,
                    mimetype=record['file_type'],
                    as_attachment=True,
                    download_name=record['original_filename']
                )

    # Unwrap User's RSA Encryption Private Key
    cursor.execute("SELECT encrypted_encryption_key_path FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    kek_hex = session.get('kek')
    if not kek_hex:
        if _wants_json():
            return jsonify({'error': 'Session encryption key unavailable'}), 401
        flash('Session encryption key expired. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        kek = bytes.fromhex(kek_hex)
        priv_enc_pem = load_encrypted_key_file(user['encrypted_encryption_key_path'], kek)

        enc_path = Path(record['encrypted_file_path'])
        if not enc_path.exists():
            return jsonify({'error': 'Encrypted media file missing from storage'}), 500

        ciphertext = enc_path.read_bytes()
        decrypted_bytes = decrypt_media_envelope(
            ciphertext=ciphertext,
            wrapped_aes_key=record['wrapped_aes_key'],
            nonce=record['nonce'],
            auth_tag=record['auth_tag'],
            owner_private_enc_key_pem=priv_enc_pem
        )
    except Exception as e:
        if _wants_json():
            return jsonify({'error': f'Decryption failed: {str(e)}'}), 500
        flash('Cryptographic decryption failed.', 'danger')
        return redirect(url_for('media.media_library'))

    # Verify Plaintext SHA-256 matches registered hash
    computed_sha256 = hashlib.sha256(decrypted_bytes).hexdigest().lower()
    if computed_sha256 != record['sha256_hash'].lower():
        if _wants_json():
            return jsonify({'error': 'Integrity failure: decrypted hash mismatch'}), 500
        flash('Integrity alert: Decrypted content hash does not match registered manifest!', 'danger')
        return redirect(url_for('media.media_library'))

    return send_file(
        io.BytesIO(decrypted_bytes),
        mimetype=record['file_type'],
        as_attachment=True,
        download_name=record['original_filename']
    )

@media_bp.route('/<media_id>/preview', methods=['GET'])
@login_required
def preview_media(media_id: str):
    """
    In-Browser Visual Preview Viewer.
    Strictly reserved for images (JPEG / PNG).
    For video files (MP4 / MOV), redirects to the secure download endpoint.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM media WHERE media_id = ?", (media_id,))
    record = cursor.fetchone()
    if not record:
        if _wants_json():
            return jsonify({'error': 'Media record not found'}), 404
        flash('Media record not found', 'danger')
        return redirect(url_for('media.media_library'))

    user_id = session.get('user_id')

    # Dual-Behavior IDOR Access Control Check (OWASP A01)
    if current_app.config.get('SECURE_MODE', True):
        if record['owner_id'] != user_id:
            if _wants_json():
                return jsonify({'error': 'Forbidden', 'message': 'Access denied: You do not own this media.'}), 403
            flash('Access denied: You do not own this media asset.', 'danger')
            return redirect(url_for('media.media_library')), 403
    else:
        # SECURE_MODE = False (Vulnerable Viva Demonstration Mode): Ownership check bypassed
        if record['owner_id'] != user_id:
            enc_path = Path(record['encrypted_file_path'])
            if enc_path.exists():
                return send_file(
                    enc_path,
                    mimetype=record['file_type'],
                    as_attachment=True,
                    download_name=record['original_filename']
                )

    # Retrieval Rule: Video formats redirect to download
    if record['file_type'] not in ('image/jpeg', 'image/png'):
        if _wants_json():
            return jsonify({
                'message': 'In-browser preview is reserved for images. Download file directly.',
                'download_url': url_for('media.download_media', media_id=media_id)
            }), 200
        flash('In-browser visual preview is reserved for images (JPG/PNG). Video assets must be downloaded directly.', 'info')
        return redirect(url_for('media.download_media', media_id=media_id))

    # Decrypt Image for in-memory Base64 data URI rendering
    cursor.execute("SELECT encrypted_encryption_key_path FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    kek_hex = session.get('kek')
    if not kek_hex:
        flash('Session encryption key expired. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        kek = bytes.fromhex(kek_hex)
        priv_enc_pem = load_encrypted_key_file(user['encrypted_encryption_key_path'], kek)
        ciphertext = Path(record['encrypted_file_path']).read_bytes()
        decrypted_bytes = decrypt_media_envelope(
            ciphertext=ciphertext,
            wrapped_aes_key=record['wrapped_aes_key'],
            nonce=record['nonce'],
            auth_tag=record['auth_tag'],
            owner_private_enc_key_pem=priv_enc_pem
        )
    except Exception as e:
        flash('Failed to decrypt image preview.', 'danger')
        return redirect(url_for('media.media_library'))

    img_b64 = base64.b64encode(decrypted_bytes).decode('utf-8')
    image_data_uri = f"data:{record['file_type']};base64,{img_b64}"

    return render_template('media/preview.html', media=dict(record), image_data_uri=image_data_uri)
