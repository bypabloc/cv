"""AdminDeleteUserIn.confirm debe matchear HARD-DELETE-USER-<user_id>.

Given un user_id valido con confirm que NO matchea ('WRONG'),
When se valida con AdminDeleteUserIn,
Then pydantic ValidationError; y el sentinel correcto queda en .confirm.
"""

import pytest
from pydantic import ValidationError


def test_admin_delete_user_in_sentinel_matches():
    from models.admin import AdminDeleteUserIn

    user_id = '01900000-0000-7000-8000-000000000abc'

    with pytest.raises(ValidationError):
        AdminDeleteUserIn.model_validate(
            {'user_id': user_id, 'confirm': 'WRONG'}
        )

    confirm = f'HARD-DELETE-USER-{user_id}'
    parsed = AdminDeleteUserIn.model_validate(
        {'user_id': user_id, 'confirm': confirm}
    )
    assert parsed.confirm == confirm
    assert str(parsed.user_id) == user_id
