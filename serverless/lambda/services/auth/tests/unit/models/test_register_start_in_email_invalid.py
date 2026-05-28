"""RegisterStartIn rechaza emails malformados.

Given un email con formato invalido,
When se valida con RegisterStartIn,
Then pydantic ValidationError (EmailStr).
"""

import pytest
from pydantic import ValidationError


def test_register_start_in_rejects_invalid_email():
    from models.register import RegisterStartIn

    with pytest.raises(ValidationError) as exc:
        RegisterStartIn(email='not-an-email', cf_turnstile_response='token-xxx')

    errors = exc.value.errors()
    assert any(e['loc'] == ('email',) for e in errors)
