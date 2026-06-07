"""
Given una request sin header Authorization (o sin prefijo Bearer),
When se invoca authenticate,
Then levanta ApplicationError 401 MISSING_AUTHORIZATION (AC-23).
"""

import pytest
import services.jwt_service as jwt_service
from shared.core.exceptions import ApplicationError


def test_jwt_authenticate_when_missing_header_then_401():
    # Arrange + Act + Assert
    with pytest.raises(ApplicationError) as exc:
        jwt_service.authenticate(None, app_config=object())

    assert exc.value.status_code == 401
    assert exc.value.code == 'MISSING_AUTHORIZATION'
