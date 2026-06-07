"""webauthn.enable reactiva un passkey -> 204.

Given un user activo y un credential_id valido,
When se invoca webauthn.enable,
Then revierte el disabled_at del credential y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_enable_ok(monkeypatch):
    """wa_svc.enable -> True -> 204."""
    from controllers.webauthn import enable as webauthn_enable

    user = _make_user(status='active')

    wa_svc = MagicMock()
    wa_svc.enable.return_value = True

    monkeypatch.setattr(
        webauthn_enable,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        webauthn_enable,
        'WebauthnService',
        lambda _c: wa_svc,
    )
    monkeypatch.setattr(
        webauthn_enable,
        'AuditService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        webauthn_enable,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(
        data={'credential_id': '01900000-0000-7000-8000-000000000001'},
    )
    result = webauthn_enable.Enable(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    assert result['data'] == {}
    wa_svc.enable.assert_called_once_with(
        user_id=user.id,
        record_id='01900000-0000-7000-8000-000000000001',
    )
