"""AdminListUsersIn.cursor exige formato UUID.

Given un cursor que no es un UUID ('not-a-uuid'),
When se valida con AdminListUsersIn,
Then pydantic ValidationError en el campo cursor.
"""

import pytest
from pydantic import ValidationError


def test_admin_list_users_in_cursor_uuid():
    from models.admin import AdminListUsersIn

    with pytest.raises(ValidationError) as exc:
        AdminListUsersIn.model_validate({'cursor': 'not-a-uuid'})
    assert any(
        e['loc'] == ('cursor',) for e in exc.value.errors()
    ), 'cursor not-a-uuid should fail but did not'
