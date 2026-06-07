"""security.overview devuelve SIEMPRE las 5 entradas -> 200.

Given un user con totp configurado, sin email_code/webauthn, con
  recovery codes (10/8) y con password,
When se invoca security.overview,
Then devuelve las 5 entradas con shape uniforme y los flags correctos.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_overview_returns_five_methods(monkeypatch):
    """security.overview -> 200 con las 5 entradas de seguridad."""
    from controllers.security import overview as security_overview

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.list_all.return_value = [
        {
            'kind': 'totp',
            'preferred': True,
            'required': True,
            'confirmed': True,
            'enabled': True,
            'created_at': '2026-01-01T00:00:00+00:00',
            'last_used_at': None,
        },
    ]
    webauthn_svc = MagicMock()
    webauthn_svc.list_all.return_value = []
    recovery_svc = MagicMock()
    recovery_svc.counts.return_value = {'total': 10, 'remaining': 8}
    password_svc = MagicMock()
    password_svc.status.return_value = {
        'has_password': True,
        'required': True,
        'last_change_at': '2026-01-01T00:00:00+00:00',
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

    totp = methods[0]
    assert totp['configured'] is True
    assert totp['enabled'] is True
    assert totp['required'] is True

    email_code = methods[1]
    assert email_code['configured'] is False

    recovery = methods[3]
    assert recovery['detail'] == {'total': 10, 'remaining': 8}

    password = methods[4]
    assert password['configured'] is True
    # AC-8: el entry password refleja el `required` real (no hardcoded false).
    assert password['required'] is True

    mfa_svc.list_all.assert_called_once_with(user_id=user.id)
    webauthn_svc.list_all.assert_called_once_with(user_id=user.id)
    recovery_svc.counts.assert_called_once_with(user_id=user.id)
    password_svc.status.assert_called_once_with(user_id=user.id)
