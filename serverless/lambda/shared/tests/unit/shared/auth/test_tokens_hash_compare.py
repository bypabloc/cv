"""
Given un magic-link token y su hash SHA-256,
When se compara con el mismo y con uno distinto,
Then compare_token devuelve True / False correctamente.
"""

import pytest

from shared.auth import compare_token, generate_opaque_token, hash_token


pytestmark = pytest.mark.unit


def test_tokens_hash_and_compare_roundtrip():
    # Arrange
    value = generate_opaque_token()
    other = generate_opaque_token()
    while other == value:
        other = generate_opaque_token()
    stored = hash_token(value)

    # Act + Assert
    assert compare_token(token=value, stored_hash=stored) is True
    assert compare_token(token=other, stored_hash=stored) is False
    assert len(stored) == 32  # SHA-256
