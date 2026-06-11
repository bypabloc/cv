"""require_active_user con user soft-deleted -> 401 USER_NOT_ACTIVE.

Given un JWT valido de un user con deleted_at seteado,
When se invoca require_active_user,
Then ApplicationError 401 USER_NOT_ACTIVE.
"""

from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from shared.core.exceptions import ApplicationError


@contextmanager
def _ctx(session):
    yield session


def test_jwt_deleted_user_401(monkeypatch):
    from services import jwt_service

    claims = SimpleNamespace(sub=uuid4(), jti=uuid4())
    monkeypatch.setattr(
        jwt_service, 'verify_jwt', lambda *_a, **_k: claims,
    )
    monkeypatch.setattr(
        jwt_service, '_is_blacklisted', lambda *_a, **_k: False,
    )
    deleted = MagicMock(deleted_at=datetime(2026, 1, 1, tzinfo=UTC))
    fake_session = MagicMock()
    fake_session.get.return_value = deleted
    monkeypatch.setattr(
        jwt_service, 'db_session', lambda: _ctx(fake_session),
    )

    config = MagicMock(jwt_secret='s', jwt_issuer='i', jwt_audience='a')
    with pytest.raises(ApplicationError) as exc:
        jwt_service.require_active_user('Bearer abc', app_config=config)

    assert exc.value.status_code == 401
    assert exc.value.code == 'USER_NOT_ACTIVE'
