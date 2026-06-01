"""LoginVerifyTotpIn exige temp_token (>= 20) + code de 6 digitos.

Given un temp_token ausente o un code no-6-digitos,
When se valida con LoginVerifyTotpIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError

_PLACEHOLDER_JWT = 'a' * 30


def test_login_verify_totp_in_rejects_missing_temp_token():
    from models.login import LoginVerifyTotpIn

    with pytest.raises(ValidationError) as exc:
        LoginVerifyTotpIn(code='123456')
    assert any(e['loc'] == ('temp_token',) for e in exc.value.errors())


def test_login_verify_totp_in_rejects_bad_code():
    from models.login import LoginVerifyTotpIn

    with pytest.raises(ValidationError) as exc:
        LoginVerifyTotpIn(temp_token=_PLACEHOLDER_JWT, code='ABC')
    assert any(e['loc'] == ('code',) for e in exc.value.errors())


def test_login_verify_totp_in_accepts_valid():
    from models.login import LoginVerifyTotpIn

    model = LoginVerifyTotpIn(temp_token=_PLACEHOLDER_JWT, code='123456')
    assert model.code == '123456'
