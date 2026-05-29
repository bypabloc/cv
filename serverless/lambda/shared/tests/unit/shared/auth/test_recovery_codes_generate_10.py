"""
Given el generador de recovery codes,
When se generan,
Then son exactamente 10, cada uno de 10 chars en el alfabeto Crockford-like.
"""

from __future__ import annotations

from shared.auth import RECOVERY_CODE_ALPHABET, generate_recovery_codes


def test_recovery_codes_generate_10() -> None:
    # Act
    codes = generate_recovery_codes()

    # Assert
    assert len(codes) == 10
    alphabet = set(RECOVERY_CODE_ALPHABET)
    for code in codes:
        assert len(code) == 10
        assert set(code) <= alphabet
