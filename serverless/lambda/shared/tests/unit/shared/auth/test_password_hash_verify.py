"""
Given una password hasheada con argon2id,
When se verifica con la misma password,
Then verify_password retorna True.
"""

import pytest

from shared.auth import hash_password, verify_password


pytestmark = pytest.mark.unit


def test_password_hash_and_verify_correct_returns_true():
    # Arrange
    password = 'correct horse battery staple'  # noqa: S105

    # Act
    hashed = hash_password(password)
    result = verify_password(password=password, hashed=hashed)

    # Assert
    assert result is True
    assert hashed.startswith('$argon2id$')
