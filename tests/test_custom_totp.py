import time
import pytest
from app.core.custom_crypto.hmac import custom_hmac_sha1, custom_hmac_sha256
from app.core.custom_crypto.totp import CustomTOTP, generate_base32_secret


def test_custom_hmac_sha1_rfc2202_vector():
    """RFC 2202 Test Case 2 for HMAC-SHA1."""
    key = b"Jefe"
    data = b"what do ya want for nothing?"
    digest = custom_hmac_sha1(key, data)
    assert digest.hex() == "effcdf6ae5eb2fa2d27416d5f184df9c259a7c79"


def test_custom_hmac_sha256_rfc4231_vector():
    """RFC 4231 Test Case 2 for HMAC-SHA256."""
    key = b"Jefe"
    data = b"what do ya want for nothing?"
    digest = custom_hmac_sha256(key, data)
    assert digest.hex() == "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"


def test_custom_totp_generation_and_verification():
    """Verify RFC 6238 TOTP generation, window verification, and URI formatting."""
    secret = generate_base32_secret()
    assert len(secret) == 32
    totp = CustomTOTP(secret)
    code = totp.now()
    assert len(code) == 6
    assert code.isdigit()
    assert totp.verify(code, valid_window=1) is True
    wrong_code = "000000" if code != "000000" else "111111"
    assert totp.verify(wrong_code, valid_window=0) is False
    uri = totp.provisioning_uri(name="alice", issuer_name="MediaGuard")
    assert uri.startswith("otpauth://totp/MediaGuard:alice?")
    assert f"secret={secret}" in uri


def test_custom_totp_rfc6238_fixed_timestamp_vector():
    """RFC 6238 Appendix B SHA-1 8-digit / 6-digit test vector at t=59 (counter=1)."""
    # Secret "12345678901234567890" in Base32 is "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    totp = CustomTOTP("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", interval=30, digits=6)
    # RFC 6238 8-digit value at t=59 is 94287082 -> 6-digit is 287082
    assert totp.at(59) == "287082"
    assert totp.verify("287082", valid_window=0, for_time=59) is True
