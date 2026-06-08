"""MfaMethodService.ensure_email_code: crea si falta, idempotente, SIN revoke.

SOLO inserta el email_code confirmado cuando el user no tiene ninguno:
- no existe -> INSERT confirmado (True).
- ya existe (confirmado y activo) -> no-op (False).
- ya existe pero deshabilitado -> no-op (False): NO se reactiva (respeta el
  disable explicito del user; re-habilitar es la accion mfa.enable).

En todos los casos NUNCA invoca SessionService.revoke_all_for_user (el
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


def test_ensure_email_code_noop_when_disabled(monkeypatch):
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
    # El user deshabilito su email_code a proposito: el backfill NO lo reactiva.
    existing = MagicMock()
    existing.confirmed_at = object()
    existing.disabled_at = object()
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
