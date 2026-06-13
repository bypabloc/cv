"""require_active_user con user disabled -> 403 ACCOUNT_DISABLED.

Given un JWT valido de un user con status DISABLED,
When se invoca require_active_user,
Then ApplicationError 403 ACCOUNT_DISABLED (no 401: el JWT es valido).
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from shared.core.exceptions import ApplicationError


@contextmanager
def _ctx(session):
    yield session


def test_jwt_disabled_403(monkeypatch):
    from services import jwt_service
    from shared.db.models.auth.enums import AuthUserStatus

    claims = SimpleNamespace(sub=uuid4(), jti=uuid4())
    monkeypatch.setattr(
        jwt_service, 'verify_jwt', lambda *_a, **_k: claims,
    )
    monkeypatch.setattr(
        jwt_service, '_is_blacklisted', lambda *_a, **_k: False,
    )
    disabled = MagicMock(deleted_at=None, status=AuthUserStatus.DISABLED)
    fake_session = MagicMock()
    fake_session.get.return_value = disabled
    monkeypatch.setattr(
        jwt_service, 'db_session', lambda: _ctx(fake_session),
    )

    config = MagicMock(jwt_secret='s', jwt_issuer='i', jwt_audience='a')
    with pytest.raises(ApplicationError) as exc:
        jwt_service.require_active_user('Bearer abc', app_config=config)

    assert exc.value.status_code == 403
    assert exc.value.code == 'ACCOUNT_DISABLED'
