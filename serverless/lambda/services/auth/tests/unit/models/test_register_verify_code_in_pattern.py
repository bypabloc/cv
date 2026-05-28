"""RegisterVerifyCodeIn rechaza codes con chars confundibles O/0/I/1/L.

Given un code que contiene `O`, `0`, `I`, `1` o `L`,
When se valida con RegisterVerifyCodeIn,
Then pydantic ValidationError (pattern mismatch).
"""

import pytest
from pydantic import ValidationError

# Placeholder de un JWT valido para el field `temp_token`
# (min_length=20). NO es un secreto real.
_PLACEHOLDER_JWT = 'a' * 30


def test_register_verify_code_in_rejects_confusing_chars():
    from models.register import RegisterVerifyCodeIn

    # El alphabet declarado en el modelo `[A-HJ-NP-Z2-9]` excluye:
    # I, O (letras confundibles con 1/0) + 0, 1 (chars excluidos via
    # rango 2-9). `L` no esta en el alphabet del modelo (es valida).
    confusing = ['OABCDEFG', '0ABCDEFG', 'IABCDEFG', '1ABCDEFG', 'aBCDEFGH']
    for code in confusing:
        with pytest.raises(ValidationError) as exc:
            RegisterVerifyCodeIn(code=code, temp_token=_PLACEHOLDER_JWT)
        errors = exc.value.errors()
        assert any(e['loc'] == ('code',) for e in errors), (
            f'code {code!r} should fail pattern but did not'
        )
