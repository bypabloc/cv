"""ProfileUpdateIn.display_name tiene max_length=64.

Given un display_name de 65 caracteres,
When se valida con ProfileUpdateIn,
Then pydantic ValidationError en el campo display_name.
"""

import pytest
from pydantic import ValidationError


def test_profile_update_in_display_name_max_64():
    from models.profile import ProfileUpdateIn

    with pytest.raises(ValidationError) as exc:
        ProfileUpdateIn.model_validate({'display_name': 'a' * 65})
    assert any(
        e['loc'] == ('display_name',) for e in exc.value.errors()
    ), 'display_name of 65 chars should fail but did not'
