"""
Given una password hasheada,
When se verifica con una password DIFERENTE,
Then verify_password retorna False.
"""

import pytest
from shared.auth import hash_password, verify_password

pytestmark = pytest.mark.unit


def test_password_verify_wrong_returns_false():
    # Arrange
    hashed = hash_password('correct password')

    # Act
    result = verify_password(password='wrong password', hashed=hashed)

    # Assert
    assert result is False
