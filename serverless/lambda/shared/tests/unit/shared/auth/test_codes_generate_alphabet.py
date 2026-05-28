"""
Given que se generan 1000 codes,
When se inspecciona cada uno,
Then todos pertenecen al CODE_ALPHABET y tienen length 8.
"""

import pytest

from shared.auth import CODE_ALPHABET, CODE_LENGTH, generate_code


pytestmark = pytest.mark.unit


def test_codes_generate_uses_alphabet_only():
    # Arrange
    iterations = 1000

    # Act
    codes = [generate_code() for _ in range(iterations)]

    # Assert
    assert len(codes) == iterations
    for code in codes:
        assert len(code) == CODE_LENGTH
        for ch in code:
            assert ch in CODE_ALPHABET
