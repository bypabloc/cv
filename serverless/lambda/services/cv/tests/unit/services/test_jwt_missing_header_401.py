"""require_active_user sin header Authorization -> 401.

Given authorization=None,
When se invoca require_active_user,
Then ApplicationError 401 MISSING_AUTHORIZATION.
"""

import pytest
from shared.core.exceptions import ApplicationError


def test_jwt_missing_header_401():
    from services import jwt_service

    with pytest.raises(ApplicationError) as exc:
        jwt_service.require_active_user(None, app_config=object())

    assert exc.value.status_code == 401
    assert exc.value.code == 'MISSING_AUTHORIZATION'
