"""LoginVerifyPasswordIn exige password >= 12 chars + temp_token >= 20.

Given una password de menos de 12 chars,
When se valida con LoginVerifyPasswordIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError

_PLACEHOLDER_JWT = 'a' * 30


def test_login_verify_password_in_rejects_short_password():
    from models.login import LoginVerifyPasswordIn

    with pytest.raises(ValidationError) as exc:
        LoginVerifyPasswordIn(
            temp_token=_PLACEHOLDER_JWT,
            password='short',
        )
    assert any(e['loc'] == ('password',) for e in exc.value.errors())


def test_login_verify_password_in_accepts_valid():
    from models.login import LoginVerifyPasswordIn

    model = LoginVerifyPasswordIn(
        temp_token=_PLACEHOLDER_JWT,
        password='a-strong-passphrase-12',
    )
    assert model.password == 'a-strong-passphrase-12'
