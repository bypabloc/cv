"""security.overview no reporta `required` un metodo NO confirmado.

Given un user con un TOTP en estado heredado inconsistente (required=True en
  la columna pero confirmed=False, sin secret confirmado para validar el code),
When se invoca security.overview,
Then la entry totp se reporta `required: False` (el login lo ignora, no debe
  mostrarse requerido). El flag real de la columna se cruza con `confirmed`.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_overview_unconfirmed_totp_reports_not_required(monkeypatch):
    """TOTP required=True pero confirmed=False -> entry required=False."""
    from controllers.security import overview as security_overview

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.list_all.return_value = [
        {
            'kind': 'totp',
            'preferred': False,
            'required': True,
            'confirmed': False,
            'enabled': True,
            'created_at': '2026-01-01T00:00:00+00:00',
            'last_used_at': None,
        },
    ]
    webauthn_svc = MagicMock()
    webauthn_svc.list_all.return_value = []
    recovery_svc = MagicMock()
    recovery_svc.counts.return_value = {'total': 0, 'remaining': 0}
    password_svc = MagicMock()
    password_svc.status.return_value = {
        'has_password': True,
        'required': True,
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

    totp = result['data']['methods'][0]
    assert totp['type'] == 'totp'
    assert totp['configured'] is True
    assert totp['enabled'] is True
    # required=True en la columna pero confirmed=False -> NO required.
    assert totp['required'] is False
    assert totp['detail'] == {'confirmed': False}
