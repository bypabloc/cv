"""require_active_user — header Authorization ausente -> 401.

Given un request sin header Authorization,
When se invoca require_active_user,
Then levanta ApplicationError con status_code 401.
"""

import pytest


def test_jwt_require_active_user_missing_header_401():
    from services import jwt_service
    from shared.core.exceptions import ApplicationError

    with pytest.raises(ApplicationError) as exc:
        jwt_service.require_active_user(None, app_config=object())

    assert exc.value.status_code == 401
