"""security.overview con user "vacio" -> email_code SIEMPRE configurado.

Given un user active sin totp/webauthn, sin recovery codes y sin password,
  pero con el email_code que el backfill (ensure_email_code) garantiza,
When se invoca security.overview,
Then las otras 4 entradas son configured=False y email_code es configured=True
  (el email se verifico en el alta; el overview hace backfill on-read).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_overview_empty_user_still_has_email_code(monkeypatch):
    """email_code SIEMPRE configurado; el resto sin configurar."""
    from controllers.security import overview as security_overview

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    # El backfill (ensure_email_code) garantiza el row email_code confirmado;
    # list_all lo refleja (simula el estado tras el backfill).
    mfa_svc.list_all.return_value = [
        {
            'kind': 'email_code',
            'preferred': False,
            'required': False,
            'confirmed': True,
            'enabled': True,
            'created_at': '2026-06-08T00:00:00+00:00',
            'last_used_at': None,
        },
    ]
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
        security_overview,
        'require_active_user',
        lambda *_a, **_k: user,
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
    assert result['code'] == 0

    methods = result['data']['methods']
    assert len(methods) == 5
    assert [m['type'] for m in methods] == [
        'totp',
        'email_code',
        'webauthn',
        'recovery_codes',
        'password',
    ]
    # email_code (indice 1) configurado por el backfill; el resto no.
    assert [m['configured'] for m in methods] == [
        False,
        True,
        False,
        False,
        False,
    ]
    # El backfill se ejecuto.
    mfa_svc.ensure_email_code.assert_called_once_with(user_id=user.id)
