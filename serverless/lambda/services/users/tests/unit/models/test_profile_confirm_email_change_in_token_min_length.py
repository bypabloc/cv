"""ProfileConfirmEmailChangeIn.token exige min_length=20.

Given un token mas corto que el minimo (19 chars),
When se valida con ProfileConfirmEmailChangeIn,
Then pydantic ValidationError en el campo token.
"""

import pytest
from pydantic import ValidationError


def test_profile_confirm_email_change_in_token_min_length():
    from models.profile import ProfileConfirmEmailChangeIn

    with pytest.raises(ValidationError) as exc:
        ProfileConfirmEmailChangeIn.model_validate({'token': 'a' * 19})
    assert any(
        e['loc'] == ('token',) for e in exc.value.errors()
    ), 'token of 19 chars should fail but did not'
