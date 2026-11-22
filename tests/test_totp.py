import pyotp
import pytest
from app.core.totp_manager import (
    generate_totp_secret,
    get_totp_uri,
    generate_totp_qr_png,
    verify_totp_code,
)

def test_generate_totp_secret():
    """Verify that generate_totp_secret produces a valid 32-character Base32 string."""
    secret1 = generate_totp_secret()
    secret2 = generate_totp_secret()

    assert isinstance(secret1, str)
    assert len(secret1) == 32
    assert secret1 != secret2

    # Verify it can be used to construct a pyotp.TOTP object without error
    totp = pyotp.TOTP(secret1)
    current_code = totp.now()
    assert len(current_code) == 6
    assert current_code.isdigit()

def test_get_totp_uri():
    """Verify that get_totp_uri formats a standard otpauth URI properly."""
    secret = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"
    username = "alice_crypto"
    uri = get_totp_uri(username, secret, issuer_name="MediaGuard")

    assert uri.startswith("otpauth://totp/MediaGuard:alice_crypto?")
    assert "secret=" + secret in uri
    assert "issuer=MediaGuard" in uri

def test_generate_totp_qr_png():
    """Verify that generate_totp_qr_png returns valid PNG bytes."""
    uri = "otpauth://totp/MediaGuard:alice?secret=JBSWY3DPEHPK3PXP&issuer=MediaGuard"
    png_bytes = generate_totp_qr_png(uri)

    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 0
    # Check PNG magic bytes: \x89PNG\r\n\x1a\n
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

def test_verify_totp_code_valid_and_invalid():
    """Verify TOTP code verification with current code, wrong code, and malformed inputs."""
    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    current_code = totp.now()

    # Valid current code
    assert verify_totp_code(secret, current_code) is True

    # Invalid code
    assert verify_totp_code(secret, "000000" if current_code != "000000" else "111111") is False
    assert verify_totp_code(secret, "abc") is False
    assert verify_totp_code(secret, "") is False
    assert verify_totp_code("", current_code) is False
