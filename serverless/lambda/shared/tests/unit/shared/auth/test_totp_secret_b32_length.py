"""
Given el generador de secret TOTP,
When se genera un secret base32,
Then tiene 32 chars y todos pertenecen al alfabeto base32 (RFC 4648).
"""

from __future__ import annotations

import string

from shared.auth.totp import generate_totp_secret_b32

_BASE32_ALPHABET = set(string.ascii_uppercase + '234567')


def test_totp_secret_b32_length() -> None:
    # Act
    b32 = generate_totp_secret_b32()

    # Assert
    assert len(b32) == 32
    assert set(b32) <= _BASE32_ALPHABET
