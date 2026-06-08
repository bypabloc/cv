"""AC-6: security.overview hace backfill on-read del email_code.

Given un user active (que pudo crearse antes de que el alta creara el
  email_code),
When consulta security.overview,
Then el controller invoca mfa_svc.ensure_email_code ANTES de leer list_all, de
  modo que el email_code queda disponible para el overview (idempotente).
"""

from unittest.mock import MagicMock, call

from .._helpers import _make_authed_event, _make_user


def test_overview_calls_ensure_email_code_before_list_all(monkeypatch):
    """El backfill (ensure_email_code) se ejecuta antes de list_all."""
    from controllers.security import overview as security_overview

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.list_all.return_value = []
    webauthn_svc = MagicMock()
    webauthn_svc.list_all.return_value = []
    recovery_svc = MagicMock()
    recovery_svc.counts.return_value = {'total': 0, 'remaining': 0}
    password_svc = MagicMock()
    password_svc.status.return_value = {
        'has_password': False,
        'required': False,
        'last_change_at': None,
    }

    monkeypatch.setattr(
        security_overview, 'require_active_user', lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        security_overview, 'MfaMethodService', lambda _c: mfa_svc,
    )
    monkeypatch.setattr(
        security_overview, 'WebauthnService', lambda _c: webauthn_svc,
    )
    monkeypatch.setattr(
        security_overview, 'RecoveryCodesService', lambda _c: recovery_svc,
    )
    monkeypatch.setattr(
        security_overview, 'PasswordService', lambda _c: password_svc,
    )
    monkeypatch.setattr(
        security_overview, 'RateLimitService', lambda _c: MagicMock(),
    )

    event = _make_authed_event()
    result = security_overview.Overview(event=event).run()

    assert result['is_valid'] is True
    # ensure_email_code se llamo una vez con el user, ANTES de list_all.
    mfa_svc.ensure_email_code.assert_called_once_with(user_id=user.id)
    assert mfa_svc.mock_calls.index(
        call.ensure_email_code(user_id=user.id),
    ) < mfa_svc.mock_calls.index(call.list_all(user_id=user.id))
