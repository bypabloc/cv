"""AC-17: webauthn.disable del unico metodo -> 409 MUST_KEEP_ONE_MFA_METHOD.

Given un user activo con total_mfa == 1,
When se invoca webauthn.disable,
Then devuelve 409 MUST_KEEP_ONE_MFA_METHOD y no llama soft_disable.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_disable_keeps_one(monkeypatch):
    """AC-17: count_active == 1 -> 409 MUST_KEEP_ONE_MFA_METHOD."""
    from controllers.webauthn import disable as webauthn_disable

    user = _make_user(status='active')

    wa_svc = MagicMock()
    wa_svc.count_active.return_value = 1

    monkeypatch.setattr(
        webauthn_disable,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        webauthn_disable,
        'WebauthnService',
        lambda _c: wa_svc,
    )
    monkeypatch.setattr(
        webauthn_disable,
        'AuditService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        webauthn_disable,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(
        data={'credential_id': '01900000-0000-7000-8000-000000000001'},
    )
    result = webauthn_disable.Disable(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4000
    assert result['status'] == 409
    assert result['data']['error'] == 'MUST_KEEP_ONE_MFA_METHOD'
    wa_svc.soft_disable.assert_not_called()
