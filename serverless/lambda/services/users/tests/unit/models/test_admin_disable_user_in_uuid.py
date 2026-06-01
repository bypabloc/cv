"""AdminDisableUserIn.user_id exige formato UUID.

Given un user_id que no es un UUID ('nope'),
When se valida con AdminDisableUserIn,
Then pydantic ValidationError en el campo user_id.
"""

import pytest
from pydantic import ValidationError


def test_admin_disable_user_in_uuid():
    from models.admin import AdminDisableUserIn

    with pytest.raises(ValidationError) as exc:
        AdminDisableUserIn.model_validate({'user_id': 'nope'})
    assert any(
        e['loc'] == ('user_id',) for e in exc.value.errors()
    ), 'user_id nope should fail but did not'
