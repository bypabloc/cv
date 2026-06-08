"""MfaMethodService.delete delega a delete_mfa del repo.

Given el repo delete_mfa devuelve True,
When se invoca delete,
Then devuelve True (el controller valida el guard MUST_KEEP_ONE antes).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_mfa_method_service_delete_returns_repo_result(monkeypatch):
    from services import mfa_method_service
    from shared.db.models.auth.enums import AuthMfaKind

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'delete_mfa',
        lambda _s, *, user_id, kind: True,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.delete(user_id='user-1', kind=AuthMfaKind.TOTP)

    assert result is True
