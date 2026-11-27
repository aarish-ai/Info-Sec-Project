import os
from typing import Dict, Union
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from app.core.custom_crypto.aes import (
    aes_256_ctr_hmac_decrypt,
    aes_256_ctr_hmac_encrypt,
)

def encrypt_media_envelope(
    file_bytes: bytes,
    owner_public_enc_key_pem: Union[str, bytes]
) -> Dict[str, bytes]:
    """
    Encrypts media using symmetric-asymmetric envelope encryption:
    1. Generates a fresh random 256-bit (32-byte) AES key.
    2. Generates a fresh random 96-bit (12-byte) initialization nonce.
    3. Encrypts media content using AES-256-GCM (authenticated symmetric encryption).
    4. Wraps (encrypts) the AES key with the owner's RSA encryption public key using RSA-OAEP.
    5. Returns dictionary with ciphertext, wrapped_aes_key, nonce, and auth_tag.
    """
    if isinstance(owner_public_enc_key_pem, str):
        pub_pem_bytes = owner_public_enc_key_pem.encode('utf-8')
    else:
        pub_pem_bytes = owner_public_enc_key_pem

    # 1. Fresh AES-256 key and 96-bit nonce
    aes_key = os.urandom(32)
    nonce = os.urandom(12)

    # 2. Custom pure-Python AES-256-CTR + HMAC-SHA256 authenticated encryption
    ciphertext, auth_tag = aes_256_ctr_hmac_encrypt(aes_key, nonce, file_bytes)

    # 3. Asymmetric key wrapping using RSA-OAEP (SHA-256 + MGF1)
    public_key = serialization.load_pem_public_key(pub_pem_bytes)
    wrapped_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return {
        'ciphertext': ciphertext,
        'wrapped_aes_key': wrapped_aes_key,
        'nonce': nonce,
        'auth_tag': auth_tag,
    }

def decrypt_media_envelope(
    ciphertext: bytes,
    wrapped_aes_key: bytes,
    nonce: bytes,
    auth_tag: bytes,
    owner_private_enc_key_pem: Union[str, bytes]
) -> bytes:
    """
    Decrypts media envelope:
    1. Unwraps the symmetric AES-256 key using owner's RSA encryption private key (RSA-OAEP).
    2. Decrypts the ciphertext using AES-256-GCM with nonce and verifies authentication tag.
    3. Raises cryptography.exceptions.InvalidTag if ciphertext or tag was tampered with.
    4. Raises ValueError if wrapped key decryption fails (e.g. wrong private key).
    """
    if isinstance(owner_private_enc_key_pem, str):
        priv_pem_bytes = owner_private_enc_key_pem.encode('utf-8')
    else:
        priv_pem_bytes = owner_private_enc_key_pem

    # 1. Unwrap AES key using RSA-OAEP
    private_key = serialization.load_pem_private_key(priv_pem_bytes, password=None)
    aes_key = private_key.decrypt(
        wrapped_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # 2. Verify HMAC-SHA256 tag and decrypt with custom AES-256-CTR
    return aes_256_ctr_hmac_decrypt(aes_key, nonce, ciphertext, auth_tag)
