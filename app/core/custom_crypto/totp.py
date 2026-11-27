"""Pure-Python RFC 4648 Base32, RFC 4226 HOTP, and RFC 6238 TOTP implementation."""
import os
import struct
import time
import urllib.parse
from typing import Optional
from app.core.custom_crypto.hmac import constant_time_compare, custom_hmac_sha1

_BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
_BASE32_MAP = {ch: idx for idx, ch in enumerate(_BASE32_ALPHABET)}


def generate_base32_secret(length: int = 32) -> str:
    """Generates a cryptographically random Base32 secret using OS CSPRNG."""
    random_bytes = os.urandom(length)
    return "".join(_BASE32_ALPHABET[b & 0x1F] for b in random_bytes)


def base32_decode(secret: str) -> bytes:
    """Decodes an RFC 4648 Base32 string (case-insensitive, ignores padding/spaces)."""
    cleaned = secret.strip().replace(" ", "").rstrip("=").upper()
    if not cleaned:
        raise ValueError("Empty Base32 secret")

    buffer = 0
    bits_left = 0
    out = bytearray()

    for ch in cleaned:
        if ch not in _BASE32_MAP:
            raise ValueError(f"Invalid Base32 character: {ch}")
        buffer = (buffer << 5) | _BASE32_MAP[ch]
        bits_left += 5
        if bits_left >= 8:
            bits_left -= 8
            out.append((buffer >> bits_left) & 0xFF)
            buffer &= (1 << bits_left) - 1

    return bytes(out)


class CustomTOTP:
    """Pure-Python RFC 6238 Time-Based One-Time Password generator & verifier."""

    def __init__(self, secret: str, interval: int = 30, digits: int = 6) -> None:
        self.secret = secret
        self.interval = interval
        self.digits = digits
        self._key = base32_decode(secret)

    def _at_counter(self, counter: int) -> str:
        msg = struct.pack(">Q", counter)
        digest = custom_hmac_sha1(self._key, msg)
        offset = digest[-1] & 0x0F
        binary = (
            ((digest[offset] & 0x7F) << 24)
            | ((digest[offset + 1] & 0xFF) << 16)
            | ((digest[offset + 2] & 0xFF) << 8)
            | (digest[offset + 3] & 0xFF)
        )
        otp = binary % (10 ** self.digits)
        return str(otp).zfill(self.digits)

    def at(self, for_time: Optional[float] = None) -> str:
        ts = time.time() if for_time is None else float(for_time)
        counter = int(ts // self.interval)
        return self._at_counter(counter)

    def now(self) -> str:
        return self.at()

    def verify(self, code: str, valid_window: int = 1, for_time: Optional[float] = None) -> bool:
        if not code or not isinstance(code, str):
            return False
        clean_code = code.strip()
        if len(clean_code) != self.digits or not clean_code.isdigit():
            return False

        ts = time.time() if for_time is None else float(for_time)
        base_counter = int(ts // self.interval)
        target_bytes = clean_code.encode("ascii")

        matched = False
        for delta in range(-valid_window, valid_window + 1):
            candidate = self._at_counter(base_counter + delta).encode("ascii")
            if constant_time_compare(candidate, target_bytes):
                matched = True
        return matched

    def provisioning_uri(self, name: str, issuer_name: str = "MediaGuard") -> str:
        label = urllib.parse.quote(f"{issuer_name}:{name}", safe=":@")
        params = urllib.parse.urlencode({
            "secret": self.secret,
            "issuer": issuer_name,
        })
        return f"otpauth://totp/{label}?{params}"
