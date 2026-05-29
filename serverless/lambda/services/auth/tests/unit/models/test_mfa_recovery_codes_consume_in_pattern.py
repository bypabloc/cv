"""MfaRecoveryCodesConsumeIn rechaza codes con chars confundibles O/0/I/1/L.

Given un recovery code que contiene O, 0, I, 1 o L,
When se valida con MfaRecoveryCodesConsumeIn,
Then pydantic ValidationError (pattern mismatch, alfabeto [A-HJ-NP-Z2-9]).
"""

import pytest
from pydantic import ValidationError

_PLACEHOLDER_JWT = 'a' * 30


def test_mfa_recovery_codes_consume_in_rejects_confusing_chars():
    from models.mfa import MfaRecoveryCodesConsumeIn

    # El alfabeto [A-HJ-NP-Z2-9] excluye I, O (letras confundibles) y 0, 1
    # (rango 2-9). `L` SI es valido (cae en el rango J-N), igual que los
    # codes de 8 chars del plan 01. Lowercase tambien falla.
    confusing = [
        'OABCDEFGHJ',
        '0ABCDEFGHJ',
        'IABCDEFGHJ',
        '1ABCDEFGHJ',
        'abcdefghjk',
    ]
    for code in confusing:
        with pytest.raises(ValidationError) as exc:
            MfaRecoveryCodesConsumeIn(
                temp_token=_PLACEHOLDER_JWT,
                code=code,
            )
        assert any(e['loc'] == ('code',) for e in exc.value.errors()), (
            f'code {code!r} should fail but did not'
        )


def test_mfa_recovery_codes_consume_in_accepts_valid_alphabet():
    from models.mfa import MfaRecoveryCodesConsumeIn

    model = MfaRecoveryCodesConsumeIn(
        temp_token=_PLACEHOLDER_JWT,
        code='ABCDEFGHJK',
    )
    assert model.code == 'ABCDEFGHJK'
