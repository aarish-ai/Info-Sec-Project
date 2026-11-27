"""Pure-Python FIPS 197 Rijndael AES-256 block cipher, CTR mode, and Encrypt-then-MAC AEAD."""
import struct
from typing import List, Tuple
from cryptography.exceptions import InvalidTag
from app.core.custom_crypto.hmac import constant_time_compare, custom_hmac_sha256
from app.core.custom_crypto.sha256 import CustomSHA256


def _gf_mul(a: int, b: int) -> int:
    """Multiply two bytes in GF(2^8) modulo x^8 + x^4 + x^3 + x + 1 (0x11B)."""
    res = 0
    for _ in range(8):
        if b & 1:
            res ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return res


def _gf_inv(a: int) -> int:
    """Multiplicative inverse in GF(2^8) via Fermat's Little Theorem (a^254)."""
    if a == 0:
        return 0
    res = 1
    base = a
    exp = 254
    while exp > 0:
        if exp & 1:
            res = _gf_mul(res, base)
        base = _gf_mul(base, base)
        exp >>= 1
    return res


def _build_sbox() -> Tuple[int, ...]:
    sbox = []
    for i in range(256):
        inv = _gf_inv(i)
        s = inv
        for shift in range(1, 5):
            s ^= ((inv << shift) | (inv >> (8 - shift))) & 0xFF
        sbox.append(s ^ 0x63)
    return tuple(sbox)


_SBOX = _build_sbox()
_XTIME2 = tuple(((i << 1) ^ (0x1B if (i & 0x80) else 0)) & 0xFF for i in range(256))
_XTIME3 = tuple(_XTIME2[i] ^ i for i in range(256))
_RCON = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)


class CustomAES256:
    """Pure-Python FIPS 197 AES-256 (14-round) block cipher."""

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("AES-256 requires a 32-byte key")
        self._round_keys = self._key_expansion(key)

    @staticmethod
    def _key_expansion(key: bytes) -> List[List[int]]:
        w: List[int] = list(struct.unpack(">8I", key))
        sbox = _SBOX
        for i in range(8, 60):
            temp = w[i - 1]
            if i % 8 == 0:
                rot = ((temp << 8) | (temp >> 24)) & 0xFFFFFFFF
                sub = (
                    (sbox[(rot >> 24) & 0xFF] << 24)
                    | (sbox[(rot >> 16) & 0xFF] << 16)
                    | (sbox[(rot >> 8) & 0xFF] << 8)
                    | sbox[rot & 0xFF]
                )
                temp = sub ^ (_RCON[(i // 8) - 1] << 24)
            elif i % 8 == 4:
                temp = (
                    (sbox[(temp >> 24) & 0xFF] << 24)
                    | (sbox[(temp >> 16) & 0xFF] << 16)
                    | (sbox[(temp >> 8) & 0xFF] << 8)
                    | sbox[temp & 0xFF]
                )
            w.append(w[i - 8] ^ temp)

        # Convert 60 32-bit words into 15 round keys of 16 bytes each (column-major)
        round_keys: List[List[int]] = []
        for r in range(15):
            rk: List[int] = []
            for word in w[r * 4:(r + 1) * 4]:
                rk.extend([
                    (word >> 24) & 0xFF,
                    (word >> 16) & 0xFF,
                    (word >> 8) & 0xFF,
                    word & 0xFF,
                ])
            round_keys.append(rk)
        return round_keys

    def encrypt_block(self, block: bytes) -> bytes:
        if len(block) != 16:
            raise ValueError("AES block size must be 16 bytes")

        sbox = _SBOX
        x2 = _XTIME2
        x3 = _XTIME3
        rks = self._round_keys

        # Initial AddRoundKey
        rk0 = rks[0]
        s = [block[i] ^ rk0[i] for i in range(16)]

        # Rounds 1..13
        for rnd in range(1, 14):
            # SubBytes + ShiftRows
            t0 = sbox[s[0]];  t1 = sbox[s[5]];  t2 = sbox[s[10]]; t3 = sbox[s[15]]
            t4 = sbox[s[4]];  t5 = sbox[s[9]];  t6 = sbox[s[14]]; t7 = sbox[s[3]]
            t8 = sbox[s[8]];  t9 = sbox[s[13]]; t10 = sbox[s[2]]; t11 = sbox[s[7]]
            t12 = sbox[s[12]]; t13 = sbox[s[1]]; t14 = sbox[s[6]]; t15 = sbox[s[11]]

            rk = rks[rnd]
            # MixColumns + AddRoundKey
            s[0]  = x2[t0]  ^ x3[t1]  ^ t2  ^ t3  ^ rk[0]
            s[1]  = t0  ^ x2[t1]  ^ x3[t2]  ^ t3  ^ rk[1]
            s[2]  = t0  ^ t1  ^ x2[t2]  ^ x3[t3]  ^ rk[2]
            s[3]  = x3[t0]  ^ t1  ^ t2  ^ x2[t3]  ^ rk[3]

            s[4]  = x2[t4]  ^ x3[t5]  ^ t6  ^ t7  ^ rk[4]
            s[5]  = t4  ^ x2[t5]  ^ x3[t6]  ^ t7  ^ rk[5]
            s[6]  = t4  ^ t5  ^ x2[t6]  ^ x3[t7]  ^ rk[6]
            s[7]  = x3[t4]  ^ t5  ^ t6  ^ x2[t7]  ^ rk[7]

            s[8]  = x2[t8]  ^ x3[t9]  ^ t10 ^ t11 ^ rk[8]
            s[9]  = t8  ^ x2[t9]  ^ x3[t10] ^ t11 ^ rk[9]
            s[10] = t8  ^ t9  ^ x2[t10] ^ x3[t11] ^ rk[10]
            s[11] = x3[t8]  ^ t9  ^ t10 ^ x2[t11] ^ rk[11]

            s[12] = x2[t12] ^ x3[t13] ^ t14 ^ t15 ^ rk[12]
            s[13] = t12 ^ x2[t13] ^ x3[t14] ^ t15 ^ rk[13]
            s[14] = t12 ^ t13 ^ x2[t14] ^ x3[t15] ^ rk[14]
            s[15] = x3[t12] ^ t13 ^ t14 ^ x2[t15] ^ rk[15]

        # Final Round 14 (no MixColumns)
        rk14 = rks[14]
        out = bytes([
            sbox[s[0]]  ^ rk14[0],  sbox[s[5]]  ^ rk14[1],  sbox[s[10]] ^ rk14[2],  sbox[s[15]] ^ rk14[3],
            sbox[s[4]]  ^ rk14[4],  sbox[s[9]]  ^ rk14[5],  sbox[s[14]] ^ rk14[6],  sbox[s[3]]  ^ rk14[7],
            sbox[s[8]]  ^ rk14[8],  sbox[s[13]] ^ rk14[9],  sbox[s[2]]  ^ rk14[10], sbox[s[7]]  ^ rk14[11],
            sbox[s[12]] ^ rk14[12], sbox[s[1]]  ^ rk14[13], sbox[s[6]]  ^ rk14[14], sbox[s[11]] ^ rk14[15],
        ])
        return out


def aes_256_ctr_encrypt(key: bytes, nonce: bytes, data: bytes) -> bytes:
    """Encrypts/decrypts arbitrary-length data using AES-256 in Counter (CTR) mode."""
    if len(nonce) != 12:
        raise ValueError("Nonce must be 12 bytes (96 bits)")
    cipher = CustomAES256(key)
    out = bytearray(len(data))
    counter = 1
    offset = 0
    total = len(data)
    while offset < total:
        ctr_block = nonce + struct.pack(">I", counter)
        keystream = cipher.encrypt_block(ctr_block)
        chunk_len = min(16, total - offset)
        for j in range(chunk_len):
            out[offset + j] = data[offset + j] ^ keystream[j]
        offset += chunk_len
        counter += 1
    return bytes(out)


aes_256_ctr_decrypt = aes_256_ctr_encrypt


def _derive_aead_subkeys(master_key: bytes) -> Tuple[bytes, bytes]:
    enc_key = CustomSHA256(master_key + b"|AES-256-CTR").digest()
    mac_key = CustomSHA256(master_key + b"|HMAC-SHA256").digest()
    return enc_key, mac_key


def aes_256_ctr_hmac_encrypt(master_key: bytes, nonce: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
    """Authenticated encryption (Encrypt-then-MAC) returning (ciphertext, 16-byte tag)."""
    enc_key, mac_key = _derive_aead_subkeys(master_key)
    ciphertext = aes_256_ctr_encrypt(enc_key, nonce, plaintext)
    tag = custom_hmac_sha256(mac_key, nonce + ciphertext)[:16]
    return ciphertext, tag


def aes_256_ctr_hmac_decrypt(master_key: bytes, nonce: bytes, ciphertext: bytes, auth_tag: bytes) -> bytes:
    """Verifies HMAC-SHA256 tag in constant time before CTR decryption; raises InvalidTag on tamper."""
    if len(nonce) != 12 or len(auth_tag) != 16:
        raise InvalidTag("Invalid nonce or authentication tag length")
    enc_key, mac_key = _derive_aead_subkeys(master_key)
    expected_tag = custom_hmac_sha256(mac_key, nonce + ciphertext)[:16]
    if not constant_time_compare(expected_tag, auth_tag):
        raise InvalidTag("Authentication tag verification failed")
    return aes_256_ctr_decrypt(enc_key, nonce, ciphertext)
