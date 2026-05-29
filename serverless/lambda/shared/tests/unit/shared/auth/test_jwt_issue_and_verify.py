"""
Given un JWT temp recien emitido,
When se verifica con el mismo secret y typ='temp',
Then retorna los claims con sub, jti, flow, step intactos.
"""

from uuid import uuid4

import pytest
from shared.auth.jwt import issue_temp_jwt, verify_jwt

pytestmark = pytest.mark.unit


def test_jwt_issue_and_verify_temp_roundtrip():
    # Arrange
    user_id = uuid4()
    secret = 'a' * 64

    # Act
    token, claims = issue_temp_jwt(
        user_id=user_id,
        flow='register',
        step=1,
        secret=secret,
    )
    verified = verify_jwt(token, secret=secret, expected_typ='temp')

    # Assert
    assert verified.sub == user_id
    assert verified.typ == 'temp'
    assert verified.flow == 'register'
    assert verified.step == 1
    assert verified.jti == claims.jti
    assert verified.exp == claims.exp
    assert verified.exp - verified.iat == 300
