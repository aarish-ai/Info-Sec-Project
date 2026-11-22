import json
from typing import Union
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

def build_canonical_manifest(
    media_id: str,
    owner_id: int,
    filename: str,
    file_size: int,
    mime_type: str,
    sha256_hash: str,
    phash: str,
    timestamp_utc: str
) -> str:
    """
    Builds a deterministic, canonical JSON representation of media registration metadata.
    Enforces sorted keys and compact separators (no whitespace) to guarantee consistent
    cryptographic digest calculation across platforms.
    """
    manifest_dict = {
        "file_size": int(file_size),
        "filename": str(filename),
        "media_id": str(media_id),
        "mime_type": str(mime_type),
        "owner_id": int(owner_id),
        "phash": str(phash),
        "sha256_hash": str(sha256_hash).lower(),
        "timestamp_utc": str(timestamp_utc)
    }
    return json.dumps(manifest_dict, sort_keys=True, separators=(',', ':'))

def sign_manifest(canonical_manifest: str, private_signing_key_pem: bytes) -> bytes:
    """
    Signs a canonical manifest string using RSA-PSS with SHA-256 and MGF1.
    """
    private_key = serialization.load_pem_private_key(
        private_signing_key_pem,
        password=None
    )
    
    manifest_bytes = canonical_manifest.encode('utf-8')
    signature = private_key.sign(
        manifest_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_manifest_signature(
    canonical_manifest: str,
    signature: bytes,
    public_signing_key_pem: Union[str, bytes]
) -> bool:
    """
    Verifies an RSA-PSS digital signature against a canonical manifest string
    using the owner's public signing key.
    Returns True if valid, False if tampered or invalid.
    """
    if isinstance(public_signing_key_pem, str):
        pem_bytes = public_signing_key_pem.encode('utf-8')
    else:
        pem_bytes = public_signing_key_pem

    try:
        public_key = serialization.load_pem_public_key(pem_bytes)
        manifest_bytes = canonical_manifest.encode('utf-8')
        public_key.verify(
            signature,
            manifest_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except (InvalidSignature, Exception):
        return False
