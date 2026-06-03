"""webauthn.disable con >1 metodo -> 204.

Given un user activo con total_mfa == 2 y un credential_id valido,
When se invoca webauthn.disable,
Then marca el disabled_at del credential y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_disable_ok(monkeypatch):
    """count_active == 2 -> soft_disable -> 204."""
    from controllers.webauthn import disable as webauthn_disable

    user = _make_user(status='active')

    wa_svc = MagicMock()
    wa_svc.count_active.return_value = 2
    wa_svc.soft_disable.return_value = True

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

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    assert result['data'] == {}
    wa_svc.soft_disable.assert_called_once_with(
        user_id=user.id,
        record_id='01900000-0000-7000-8000-000000000001',
    )
