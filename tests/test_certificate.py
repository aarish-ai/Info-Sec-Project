import io
import pytest
from app.core.certificate import generate_verification_certificate_pdf

def test_generate_verification_certificate_pdf_valid():
    media_record = {
        'media_id': '4b8d7a12-8e1e-458b-9a41-2c938f4d9201',
        'owner_username': 'alice_investigator',
        'original_filename': 'crime_scene_photo_01.jpg',
        'file_size': 2048576,
        'file_type': 'image/jpeg',
        'sha256_hash': '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae',
        'phash': 'a1b2c3d4e5f60718',
        'registration_timestamp': '2026-11-22T14:30:00Z',
    }
    base_url = 'https://mediaguard.local'

    pdf_bytes = generate_verification_certificate_pdf(media_record, base_url)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b'%PDF-')
    # Valid PDF terminates with %%EOF or has PDF structures
    assert b'%%EOF' in pdf_bytes or b'xref' in pdf_bytes

def test_generate_certificate_with_missing_optional_fields():
    # Test record with minimal keys (e.g. without owner_username, fallback to owner_id)
    minimal_record = {
        'media_id': '8e4f1a23-4567-89ab-cdef-0123456789ab',
        'owner_id': 42,
        'original_filename': 'document.png',
        'file_size': 512,
        'file_type': 'image/png',
        'sha256_hash': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        'phash': 'N/A',
        'registration_timestamp': '2026-11-22 12:00:00',
    }
    pdf_bytes = generate_verification_certificate_pdf(minimal_record, 'https://mediaguard.local')

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b'%PDF-')
