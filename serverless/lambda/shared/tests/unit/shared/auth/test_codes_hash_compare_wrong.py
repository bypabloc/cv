"""
Given un code generado y su hash,
When se compara con un code DIFERENTE,
Then compare_code retorna False.
"""

import pytest

from shared.auth import compare_code, generate_code, hash_code


pytestmark = pytest.mark.unit


def test_codes_hash_and_compare_wrong_returns_false():
    # Arrange
    correct_code = generate_code()
    wrong_code = generate_code()
    stored_hash = hash_code(correct_code)

    # Act
    result = compare_code(code=wrong_code, stored_hash=stored_hash)

    # Assert
    assert result is False
