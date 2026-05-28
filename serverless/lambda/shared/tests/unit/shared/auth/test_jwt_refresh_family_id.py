"""
Given un JWT refresh emitido con family_id,
When se verifica,
Then los claims preservan exactamente el family_id provisto.
"""

from uuid import uuid4

import pytest

from shared.auth import issue_refresh_jwt, verify_jwt


pytestmark = pytest.mark.unit


def test_jwt_refresh_preserves_family_id():
    # Arrange
    secret = 'a' * 64
    user_id = uuid4()
    family_id = uuid4()

    # Act
    token, claims = issue_refresh_jwt(
        user_id=user_id, family_id=family_id, secret=secret,
    )
    verified = verify_jwt(token, secret=secret, expected_typ='refresh')

    # Assert
    assert verified.family_id == family_id
    assert claims.family_id == family_id
    assert verified.typ == 'refresh'
    assert verified.sub == user_id
    # refresh TTL = 30 dias en segundos
    assert verified.exp - verified.iat == 30 * 24 * 3600
