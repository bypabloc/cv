"""MfaConfirmTotpIn exige code de exactamente 6 digitos.

Given un code que no es 6 digitos (letras, longitud distinta),
When se valida con MfaConfirmTotpIn,
Then pydantic ValidationError (pattern mismatch).
"""

import pytest
from pydantic import ValidationError


def test_mfa_confirm_totp_in_rejects_non_6_digits():
    from models.mfa import MfaConfirmTotpIn

    invalid = ['12345', '1234567', 'ABCDEF', '12 456', '']
    for code in invalid:
        with pytest.raises(ValidationError) as exc:
            MfaConfirmTotpIn(code=code)
        assert any(e['loc'] == ('code',) for e in exc.value.errors()), (
            f'code {code!r} should fail but did not'
        )


def test_mfa_confirm_totp_in_accepts_6_digits():
    from models.mfa import MfaConfirmTotpIn

    model = MfaConfirmTotpIn(code='123456')
    assert model.code == '123456'
