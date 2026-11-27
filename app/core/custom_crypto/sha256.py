"""Pure-Python FIPS 180-4 SHA-256 implementation with streaming chunk support."""
import math
import struct
from typing import List, Optional


def _generate_primes(count: int) -> List[int]:
    primes: List[int] = []
    candidate = 2
    while len(primes) < count:
        is_prime = True
        limit = int(math.isqrt(candidate))
        for p in primes:
            if p > limit:
                break
            if candidate % p == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
        candidate += 1
    return primes


_PRIMES_64 = _generate_primes(64)

# Initial hash values: first 32 bits of fractional parts of sqrt of first 8 primes
_INITIAL_H = tuple(
    int((math.sqrt(p) % 1.0) * (1 << 32)) & 0xFFFFFFFF
    for p in _PRIMES_64[:8]
)

# Round constants: first 32 bits of fractional parts of cube roots of first 64 primes
_K = tuple(
    int(((p ** (1.0 / 3.0)) % 1.0) * (1 << 32)) & 0xFFFFFFFF
    for p in _PRIMES_64
)


def _rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


class CustomSHA256:
    """Streaming FIPS 180-4 SHA-256 hasher implemented in pure Python."""

    block_size = 64
    digest_size = 32

    def __init__(self, initial_data: Optional[bytes] = None) -> None:
        self._state = list(_INITIAL_H)
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
        for i in range(16, 64):
            s0 = _rotr(w[i - 15], 7) ^ _rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
            s1 = _rotr(w[i - 2], 17) ^ _rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w.append((w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFF)

        a, b, c, d, e, f, g, h = self._state
        k = _K

        for i in range(64):
            big_s1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ ((~e) & g)
            temp1 = (h + big_s1 + ch + k[i] + w[i]) & 0xFFFFFFFF
            big_s0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (big_s0 + maj) & 0xFFFFFFFF

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        self._state[0] = (self._state[0] + a) & 0xFFFFFFFF
        self._state[1] = (self._state[1] + b) & 0xFFFFFFFF
        self._state[2] = (self._state[2] + c) & 0xFFFFFFFF
        self._state[3] = (self._state[3] + d) & 0xFFFFFFFF
        self._state[4] = (self._state[4] + e) & 0xFFFFFFFF
        self._state[5] = (self._state[5] + f) & 0xFFFFFFFF
        self._state[6] = (self._state[6] + g) & 0xFFFFFFFF
        self._state[7] = (self._state[7] + h) & 0xFFFFFFFF

    def _finalize(self) -> List[int]:
        saved_state = list(self._state)
        saved_buffer = bytearray(self._buffer)

        bit_len = self._total_bytes * 8
        self._buffer.append(0x80)
        while (len(self._buffer) % 64) != 56:
            self._buffer.append(0x00)
        self._buffer.extend(struct.pack(">Q", bit_len))

        for offset in range(0, len(self._buffer), 64):
            self._compress(self._buffer[offset:offset + 64])

        final_state = list(self._state)
        self._state = saved_state
        self._buffer = saved_buffer
        return final_state

    def digest(self) -> bytes:
        return struct.pack(">8I", *self._finalize())

    def hexdigest(self) -> str:
        return "".join(f"{word:08x}" for word in self._finalize())
