"""MfaMethodService.disable delega a disable_mfa del repo.

Given el repo disable_mfa devuelve True,
When se invoca disable,
Then devuelve True (el controller valida el count antes).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_mfa_method_service_disable_returns_repo_result(monkeypatch):
    from services import mfa_method_service
    from shared.db.models import AuthMfaKind

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'disable_mfa',
        lambda _s, *, user_id, kind: True,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.disable(user_id='user-1', kind=AuthMfaKind.EMAIL_CODE)

    assert result is True
