"""require_active_user — user DISABLED -> 403.

Given un access JWT valido pero el user esta disabled,
When se invoca require_active_user,
Then levanta ApplicationError con status_code 403.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest


@contextmanager
def _ctx(session):
    yield session


def test_jwt_require_active_user_disabled_403(monkeypatch):
    from services import jwt_service
    from shared.core import ApplicationError
    from shared.db.models import AuthUserStatus

    claims = SimpleNamespace(sub=uuid4(), family_id='fam-1')
    fake_jwt = MagicMock()
    fake_jwt.verify.return_value = claims
    monkeypatch.setattr(jwt_service, 'JwtService', lambda _c: fake_jwt)

    disabled = MagicMock(deleted_at=None, status=AuthUserStatus.DISABLED)
    fake_session = MagicMock()
    fake_session.get.return_value = disabled
    monkeypatch.setattr(
        jwt_service, 'db_session', lambda: _ctx(fake_session),
    )

    with pytest.raises(ApplicationError) as exc:
        jwt_service.require_active_user('Bearer abc', app_config=object())

    assert exc.value.status_code == 403
