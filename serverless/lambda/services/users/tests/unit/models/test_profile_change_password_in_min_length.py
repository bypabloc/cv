"""ProfileChangePasswordIn exige min_length=12 en new_password.

Given un new_password de 11 chars (bajo el minimo de 12),
When se valida con ProfileChangePasswordIn,
Then pydantic ValidationError en el campo new_password.
"""

import pytest
from pydantic import ValidationError


def test_profile_change_password_in_min_length():
    from models.profile import ProfileChangePasswordIn

    with pytest.raises(ValidationError) as exc:
        ProfileChangePasswordIn.model_validate(
            {
                'current_password': 'current-pass-12',
                'new_password': 'short-11-ch',
            },
        )
    assert any(
        e['loc'] == ('new_password',) for e in exc.value.errors()
    ), 'new_password 11 chars should fail min_length but did not'
