"""security.overview con user sin metodos -> 5 entradas no configuradas.

Given un user sin totp/email_code/webauthn, sin recovery codes y sin
  password,
When se invoca security.overview,
Then devuelve las 5 entradas con configured=False.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_overview_empty_user(monkeypatch):
    """security.overview sin metodos -> 5 entradas configured=False."""
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
    assert [m['configured'] for m in methods] == [
        False,
        False,
        False,
        False,
        False,
    ]
