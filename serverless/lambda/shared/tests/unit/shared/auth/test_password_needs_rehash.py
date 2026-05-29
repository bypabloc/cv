"""
Given un hash argon2id con parametros antiguos (memory_cost menor),
When se verifica con la password correcta,
Then verify_password levanta NeedsRehashError.
"""

import pytest
from argon2 import PasswordHasher
from shared.auth import NeedsRehashError, verify_password

pytestmark = pytest.mark.unit

_PWD = 'something-strong-for-test'


def test_password_with_old_params_raises_needs_rehash():
    # Arrange: hash con time_cost=1, memory_cost=2^14 (mas debiles que el
    # default time_cost=3, memory_cost=2^16). Argon2 detecta este hash
    # como "necesita rehash" al verificarlo con el PasswordHasher default.
    weak_hasher = PasswordHasher(time_cost=1, memory_cost=2**14, parallelism=1)
    old_hash = weak_hasher.hash(_PWD)

    # Act + Assert
    with pytest.raises(NeedsRehashError):
        verify_password(password=_PWD, hashed=old_hash)
