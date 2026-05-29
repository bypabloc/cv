"""
Given un code y su hash SHA-256,
When se compara el code con el hash,
Then compare_code retorna True.
"""

import pytest
from shared.auth import compare_code, generate_code, hash_code

pytestmark = pytest.mark.unit


def test_codes_hash_and_compare_correct_returns_true():
    # Arrange
    code = generate_code()
    stored_hash = hash_code(code)

    # Act
    result = compare_code(code=code, stored_hash=stored_hash)

    # Assert
    assert result is True
    assert len(stored_hash) == 32  # SHA-256
