"""Pure-Python RFC 2104 HMAC and FIPS 180-4 SHA-1 primitives."""
import struct
from typing import Callable, Optional
from app.core.custom_crypto.sha256 import CustomSHA256


def _rotl32(x: int, n: int) -> int:
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


class CustomSHA1:
    """Pure-Python FIPS 180-4 SHA-1 hasher (used for RFC 4226/6238 TOTP HMAC-SHA1)."""

    block_size = 64
    digest_size = 20

    def __init__(self, initial_data: Optional[bytes] = None) -> None:
        self._state = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
        self._buffer = bytearray()
        self._total_bytes = 0
        if initial_data:
            self.update(initial_data)

    def update(self, data: bytes) -> None:
        if not data:
            return
        if isinstance(data, memoryview):
            data = data.tobytes()
        self._total_bytes += len(data)
        self._buffer.extend(data)

        offset = 0
        buf_len = len(self._buffer)
        while offset + 64 <= buf_len:
            self._compress(self._buffer[offset:offset + 64])
            offset += 64
        if offset:
            del self._buffer[:offset]

    def _compress(self, block: bytes) -> None:
        w = list(struct.unpack(">16I", block))
        for i in range(16, 80):
            w.append(_rotl32(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1))

        a, b, c, d, e = self._state
        for i in range(80):
            if i < 20:
                f = (b & c) | ((~b) & d)
                k = 0x5A827999
            elif i < 40:
                f = b ^ c ^ d
                k = 0x6ED9EBA1
            elif i < 60:
                f = (b & c) | (b & d) | (c & d)
                k = 0x8F1BBCDC
            else:
                f = b ^ c ^ d
                k = 0xCA62C1D6

            temp = (_rotl32(a, 5) + f + e + k + w[i]) & 0xFFFFFFFF
            e = d
            d = c
            c = _rotl32(b, 30)
            b = a
            a = temp

        self._state[0] = (self._state[0] + a) & 0xFFFFFFFF
        self._state[1] = (self._state[1] + b) & 0xFFFFFFFF
        self._state[2] = (self._state[2] + c) & 0xFFFFFFFF
        self._state[3] = (self._state[3] + d) & 0xFFFFFFFF
        self._state[4] = (self._state[4] + e) & 0xFFFFFFFF

    def digest(self) -> bytes:
        saved_state = list(self._state)
        saved_buffer = bytearray(self._buffer)

        bit_len = self._total_bytes * 8
        self._buffer.append(0x80)
        while (len(self._buffer) % 64) != 56:
            self._buffer.append(0x00)
        self._buffer.extend(struct.pack(">Q", bit_len))

        for offset in range(0, len(self._buffer), 64):
            self._compress(self._buffer[offset:offset + 64])

        out = struct.pack(">5I", *self._state)
        self._state = saved_state
        self._buffer = saved_buffer
        return out

    def hexdigest(self) -> str:
        return self.digest().hex()


def custom_hmac(key: bytes, message: bytes, hash_cls: Callable) -> bytes:
    """RFC 2104 Keyed-Hash Message Authentication Code."""
    block_size = hash_cls.block_size
    if len(key) > block_size:
        key = hash_cls(key).digest()
    if len(key) < block_size:
        key = key + b"\x00" * (block_size - len(key))

    ipad = bytes(b ^ 0x36 for b in key)
    opad = bytes(b ^ 0x5C for b in key)

    inner = hash_cls(ipad + message).digest()
    return hash_cls(opad + inner).digest()


def custom_hmac_sha1(key: bytes, message: bytes) -> bytes:
    return custom_hmac(key, message, CustomSHA1)


def custom_hmac_sha256(key: bytes, message: bytes) -> bytes:
    return custom_hmac(key, message, CustomSHA256)


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """Constant-time byte/string equality check to mitigate timing side-channels."""
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= x ^ y
    return diff == 0
