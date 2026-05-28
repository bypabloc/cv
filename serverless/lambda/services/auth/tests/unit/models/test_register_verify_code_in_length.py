"""RegisterVerifyCodeIn rechaza codes que NO miden exactamente 8 chars.

Given un code de 7 chars o 9 chars (con alphabet valido),
When se valida con RegisterVerifyCodeIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError

_PLACEHOLDER_JWT = 'a' * 30


def test_register_verify_code_in_rejects_wrong_length():
    from models.register import RegisterVerifyCodeIn

    for code in ('ABCDEFG', 'ABCDEFGHJ'):
        with pytest.raises(ValidationError):
            RegisterVerifyCodeIn(code=code, temp_token=_PLACEHOLDER_JWT)
