"""Pure-Python Keccak-256 (the hash Ethereum / Solidity keccak256 uses).

Stdlib ``hashlib.sha3_256`` is NIST SHA-3, *not* Keccak-256 — the two differ
in padding, so it cannot be used for contract call data. This module is
self-contained (no new dependency) and is verified against the standard
test vectors in tests/test_record.py.
"""

from __future__ import annotations

_MASK64 = (1 << 64) - 1

# Round constants for Keccak-f[1600] (24 rounds).
_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

# Rotation offsets r[x][y], indexed [y][x].
_RHO = [
    [0, 1, 62, 28, 27],
    [36, 44, 6, 55, 20],
    [3, 10, 43, 25, 39],
    [41, 45, 15, 21, 8],
    [18, 2, 61, 56, 14],
]


def _rol(x: int, n: int) -> int:
    if n == 0:
        return x & _MASK64
    return ((x << n) | (x >> (64 - n))) & _MASK64


def _keccak_f(state: list[int]) -> list[int]:
    for rnd in range(24):
        # Theta
        c = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
             for x in range(5)]
        d = [c[(x + 4) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        state = [state[i] ^ d[i % 5] for i in range(25)]
        # Rho + Pi
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(state[x + 5 * y], _RHO[y][x])
        # Chi
        for y in range(5):
            row = b[5 * y:5 * y + 5]
            for x in range(5):
                state[5 * y + x] = row[x] ^ (~row[(x + 1) % 5] & row[(x + 2) % 5])
        # Iota
        state[0] ^= _RC[rnd]
    return state


def keccak256(data: bytes) -> bytes:
    """Return the 32-byte Keccak-256 digest of *data*."""
    rate = 136  # bytes (1088 bits) for Keccak-256
    state = [0] * 25
    # Absorb full blocks.
    offset = 0
    while offset + rate <= len(data):
        block = data[offset:offset + rate]
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(block[i * 8:(i + 1) * 8], "little")
        state = _keccak_f(state)
        offset += rate
    # Final block: pad10*1 with domain suffix 0x01 (Keccak, not SHA-3's 0x06).
    tail = bytearray(data[offset:])
    tail.append(0x01)
    while len(tail) < rate:
        tail.append(0x00)
    tail[-1] |= 0x80
    for i in range(rate // 8):
        state[i] ^= int.from_bytes(bytes(tail[i * 8:(i + 1) * 8]), "little")
    state = _keccak_f(state)
    return b"".join(state[i].to_bytes(8, "little") for i in range(4))
