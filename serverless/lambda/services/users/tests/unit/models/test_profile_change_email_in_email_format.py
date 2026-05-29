"""ProfileChangeEmailIn.new_email valida formato de email (EmailStr).

Given un new_email con formato invalido ('not-an-email'),
When se valida con ProfileChangeEmailIn,
Then pydantic ValidationError en el campo new_email.
"""

import pytest
from pydantic import ValidationError


def test_profile_change_email_in_email_format():
    from models.profile import ProfileChangeEmailIn

    with pytest.raises(ValidationError) as exc:
        ProfileChangeEmailIn.model_validate({'new_email': 'not-an-email'})
    assert any(
        e['loc'] == ('new_email',) for e in exc.value.errors()
    ), 'new_email not-an-email should fail but did not'
