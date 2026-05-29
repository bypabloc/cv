"""
Given un credential con sign_count=5,
When se llama update_sign_count con new_count=6 (avanza) y con 3 (regresa),
Then 6 -> True y actualiza; 3 -> False y NO actualiza.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.models import AuthWebauthnCredential
from shared.db.repositories.auth_mfa import update_sign_count

pytestmark = pytest.mark.unit


def test_update_sign_count_only_when_greater():
    # Arrange
    session = MagicMock()
    cred = AuthWebauthnCredential(
        user_id='u1',
        credential_id=b'cid',
        public_key=b'pk',
        sign_count=5,
    )
    session.execute.return_value.scalar_one_or_none.return_value = cred

    # Act / Assert — avanza.
    assert update_sign_count(session, credential_id=b'cid', new_count=6) is True
    assert cred.sign_count == 6

    # Act / Assert — regresa (no debe actualizar).
    assert (
        update_sign_count(session, credential_id=b'cid', new_count=3) is False
    )
    assert cred.sign_count == 6
