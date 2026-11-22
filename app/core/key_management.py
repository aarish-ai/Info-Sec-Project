import os
from pathlib import Path
from typing import Dict, Tuple, Union
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def generate_salt(length: int = 16) -> bytes:
    """Generate cryptographically secure random bytes for KDF salt."""
    return os.urandom(length)

def generate_user_key_pairs(key_size: int = 2048) -> Dict[str, bytes]:
    """
    Generates TWO distinct RSA key pairs to satisfy the Key Separation Principle:
    1. Digital Signing Key Pair (RSA-PSS)
    2. Asymmetric Encryption Key Pair (RSA-OAEP)

    Returns a dictionary of PEM-encoded bytes for both public and private keys.
    """
    # 1. Generate Signing Key Pair
    signing_priv = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    signing_priv_pem = signing_priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    signing_pub_pem = signing_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # 2. Generate Separate Encryption Key Pair
    encryption_priv = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    encryption_priv_pem = encryption_priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    encryption_pub_pem = encryption_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return {
        'signing_private_pem': signing_priv_pem,
        'signing_public_pem': signing_pub_pem,
        'encryption_private_pem': encryption_priv_pem,
        'encryption_public_pem': encryption_pub_pem,
    }

def derive_kek(password: str, salt: bytes, length: int = 32) -> bytes:
    """
    Derives a Key Encryption Key (KEK) using scrypt (N=2^14, r=8, p=1).
    Used to encrypt user RSA private keys at rest.
    """
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
    else:
        password_bytes = password

    kdf = Scrypt(
        salt=salt,
        length=length,
        n=2**14,      # 16384 CPU/memory cost
        r=8,          # Block size
        p=1           # Parallelization parameter
    )
    return kdf.derive(password_bytes)

def encrypt_private_key(private_pem: bytes, kek: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypts a private key PEM using AES-256-GCM.
    Returns:
        (ciphertext, nonce, tag)
    """
    nonce = os.urandom(12)  # 96-bit standard AES-GCM nonce
    aesgcm = AESGCM(kek)
    combined = aesgcm.encrypt(nonce, private_pem, associated_data=None)
    # Combined output from cryptography AESGCM is ciphertext + 16-byte auth tag
    ciphertext = combined[:-16]
    tag = combined[-16:]
    return ciphertext, nonce, tag

def decrypt_private_key(ciphertext: bytes, nonce: bytes, tag: bytes, kek: bytes) -> bytes:
    """
    Decrypts an AES-256-GCM encrypted private key PEM and verifies authentication tag.
    Raises cryptography.exceptions.InvalidTag if ciphertext or tag is modified.
    """
    aesgcm = AESGCM(kek)
    combined = ciphertext + tag
    return aesgcm.decrypt(nonce, combined, associated_data=None)

def save_encrypted_key_file(file_path: Union[str, Path], ciphertext: bytes, nonce: bytes, tag: bytes) -> None:
    """Saves encrypted private key file containing nonce (12 bytes) + tag (16 bytes) + ciphertext."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(nonce + tag + ciphertext)

def load_encrypted_key_file(file_path: Union[str, Path], kek: bytes) -> bytes:
    """Reads encrypted private key file, extracts nonce, tag, and ciphertext, and decrypts PEM using kek."""
    path = Path(file_path)
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) < 28:
        raise ValueError("Corrupt key file: payload too short for nonce and tag")
    nonce = data[:12]
    tag = data[12:28]
    ciphertext = data[28:]
    return decrypt_private_key(ciphertext, nonce, tag, kek)
