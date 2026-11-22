import io
import os
from datetime import datetime, timezone
from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    render_template,
    flash,
)
from werkzeug.utils import secure_filename
from app.database.db import get_db
from app.core.hashing import compute_streamed_sha256, compute_phash, compute_phash_distance
from app.core.signatures import verify_manifest_signature

verify_bp = Blueprint('verify', __name__, url_prefix='/verify')

def _wants_json():
    """Determine whether the request expects a JSON API response."""
    return (
        request.is_json
        or request.path.startswith('/api/')
        or 'application/json' in request.headers.get('Accept', '')
    )

@verify_bp.route('', methods=['GET', 'POST'])
@verify_bp.route('/', methods=['GET', 'POST'])
def verify():
    """
    Universal Public Verification Portal.
    Allows guests and authenticated users alike to verify any media file
    against registered provenance certificates.

    Outcomes:
        - AUTHENTIC: SHA-256 matches & RSA-PSS digital signature is valid.
        - MODIFIED: SHA-256 differs (tampered/altered) & RSA-PSS signature is valid.
        - INVALID_SIGNATURE: Digital signature check failed (manifest forged).
        - UNKNOWN: Media / Certificate ID does not exist in registry.
    """
    if request.method == 'GET':
        cert_id = (request.args.get('cert_id') or request.args.get('media_id') or '').strip()
        if _wants_json():
            return jsonify({'message': 'Submit multipart form with cert_id and file to /verify'}), 200
        return render_template('verify/verify.html', cert_id=cert_id)

    # POST verification handling
    cert_id = (request.form.get('cert_id') or request.form.get('media_id') or '').strip()
    file_storage = request.files.get('file') or request.files.get('media')

    if not cert_id or not file_storage or not file_storage.filename.strip():
        if _wants_json():
            return jsonify({'error': 'Both cert_id and a valid file are required for verification'}), 400
        flash('Both Certificate / Media ID and the file to inspect are required.', 'danger')
        return render_template('verify/verify.html', cert_id=cert_id), 400

    filename = secure_filename(file_storage.filename)
    db = get_db()
    cursor = db.cursor()

    # Query registered media record and owner's public signing key
    cursor.execute(
        """
        SELECT m.*, u.username as owner_username, u.public_signing_key
        FROM media m
        JOIN users u ON m.owner_id = u.user_id
        WHERE m.media_id = ?
        """,
        (cert_id,)
    )
    record = cursor.fetchone()

    # 1. Outcome: UNKNOWN
    if not record:
        if _wants_json():
            return jsonify({
                'verdict': 'UNKNOWN',
                'media_id': cert_id,
                'message': 'No registered media asset found matching this Certificate ID.'
            }), 200

        return render_template(
            'verify/result.html',
            verdict='UNKNOWN',
            cert_id=cert_id,
            submitted_filename=filename
        ), 200

    # 2. Compute Hashes on uploaded file
    submitted_sha256 = compute_streamed_sha256(file_storage)
    submitted_phash = compute_phash(file_storage)

    # 3. Dual-Check Verification
    # Check 1: File integrity
    hash_match = (submitted_sha256.lower() == record['sha256_hash'].lower())

    # Check 2: Provenance authenticity & manifest signature
    signature_valid = verify_manifest_signature(
        canonical_manifest=record['registration_manifest'],
        signature=record['digital_signature'],
        public_signing_key_pem=record['public_signing_key']
    )

    # Diagnostic Check: Perceptual Hash distance
    phash_distance = compute_phash_distance(record['phash'], submitted_phash)

    # 4. Synthesize Final Verdict
    if not signature_valid:
        verdict = 'INVALID_SIGNATURE'
    elif hash_match:
        verdict = 'AUTHENTIC'
    else:
        verdict = 'MODIFIED'

    # 5. Record attempt in verification_history table
    verifier_id = session.get('user_id')
    timestamp_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute(
        """
        INSERT INTO verification_history (
            media_id, verifier_user_id, uploaded_filename, submitted_sha256,
            submitted_phash, hash_match, signature_valid, phash_distance,
            overall_status, verification_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record['media_id'],
            verifier_id,
            filename,
            submitted_sha256,
            submitted_phash,
            1 if hash_match else 0,
            1 if signature_valid else 0,
            phash_distance if phash_distance >= 0 else None,
            verdict,
            timestamp_str
        )
    )
    db.commit()

    if _wants_json():
        return jsonify({
            'verdict': verdict,
            'media_id': record['media_id'],
            'original_filename': record['original_filename'],
            'owner_username': record['owner_username'],
            'registered_sha256': record['sha256_hash'],
            'submitted_sha256': submitted_sha256,
            'registered_phash': record['phash'],
            'submitted_phash': submitted_phash,
            'hash_match': hash_match,
            'signature_valid': signature_valid,
            'phash_distance': phash_distance,
            'registration_timestamp': str(record['registration_timestamp']),
            'verification_timestamp': timestamp_str
        }), 200

    return render_template(
        'verify/result.html',
        verdict=verdict,
        cert_id=record['media_id'],
        record=dict(record),
        submitted_filename=filename,
        submitted_sha256=submitted_sha256,
        submitted_phash=submitted_phash,
        hash_match=hash_match,
        signature_valid=signature_valid,
        phash_distance=phash_distance,
        verification_timestamp=timestamp_str
    ), 200
