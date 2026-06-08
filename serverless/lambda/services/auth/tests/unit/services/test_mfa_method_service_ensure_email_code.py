"""MfaMethodService.ensure_email_code: idempotente, confirmado, SIN revoke.

Garantiza un email_code confirmado y activo. Tres caminos:
- no existe -> INSERT confirmado (True).
- existe confirmado y activo -> no-op (False).
- existe no-confirmado o deshabilitado -> re-confirma via confirm_mfa (True).

En LOS TRES casos NUNCA invoca SessionService.revoke_all_for_user (el
email_code del alta no es el "primer MFA fuerte").
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


def _patch_session(monkeypatch, session):
    from services import mfa_method_service

    @contextmanager
    def _fake_session():
        yield session

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    fake_session_svc = MagicMock()
    monkeypatch.setattr(
        mfa_method_service,
        'SessionService',
        lambda _c: fake_session_svc,
    )
    return fake_session_svc


def test_ensure_email_code_creates_when_missing(monkeypatch):
    from services import mfa_method_service

    session = MagicMock()
    session_svc = _patch_session(monkeypatch, session)
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: None,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.ensure_email_code(user_id='u-1')

    assert result is True
    session.add.assert_called_once()
    session_svc.revoke_all_for_user.assert_not_called()


def test_ensure_email_code_noop_when_confirmed_active(monkeypatch):
    from services import mfa_method_service

    session = MagicMock()
    session_svc = _patch_session(monkeypatch, session)
    confirm_called = {'n': 0}
    monkeypatch.setattr(
        mfa_method_service,
        'confirm_mfa',
        lambda _s, *, user_id, kind: confirm_called.update(
            n=confirm_called['n'] + 1,
        ),
    )
    existing = MagicMock()
    existing.confirmed_at = object()
    existing.disabled_at = None
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: existing,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.ensure_email_code(user_id='u-1')

    assert result is False
    session.add.assert_not_called()
    assert confirm_called['n'] == 0
    session_svc.revoke_all_for_user.assert_not_called()


def test_ensure_email_code_reconfirms_when_disabled(monkeypatch):
    from services import mfa_method_service

    session = MagicMock()
    session_svc = _patch_session(monkeypatch, session)
    confirm_args = {}
    monkeypatch.setattr(
        mfa_method_service,
        'confirm_mfa',
        lambda _s, *, user_id, kind: confirm_args.update(
            user_id=user_id, kind=kind,
        ),
    )
    existing = MagicMock()
    existing.confirmed_at = None
    existing.disabled_at = object()
    monkeypatch.setattr(
        mfa_method_service,
        'get_mfa_method',
        lambda _s, *, user_id, kind: existing,
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.ensure_email_code(user_id='u-1')

    assert result is True
    from shared.db.models.auth.enums import AuthMfaKind

    assert confirm_args == {'user_id': 'u-1', 'kind': AuthMfaKind.EMAIL_CODE}
    session.add.assert_not_called()
    session_svc.revoke_all_for_user.assert_not_called()
