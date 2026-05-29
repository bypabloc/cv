"""AdminListUsersIn.page_size tiene le=200.

Given un page_size por encima del maximo (201),
When se valida con AdminListUsersIn,
Then pydantic ValidationError; y page_size=200 queda en .page_size.
"""

import pytest
from pydantic import ValidationError


def test_admin_list_users_in_page_size_max():
    from models.admin import AdminListUsersIn

    with pytest.raises(ValidationError) as exc:
        AdminListUsersIn.model_validate({'page_size': 201})
    assert any(
        e['loc'] == ('page_size',) for e in exc.value.errors()
    ), 'page_size 201 should fail but did not'

    parsed = AdminListUsersIn.model_validate({'page_size': 200})
    assert parsed.page_size == 200
