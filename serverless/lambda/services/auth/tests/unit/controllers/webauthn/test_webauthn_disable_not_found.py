"""webauthn.disable de un credential inexistente -> 404 NOT_FOUND.

Given un user activo con total_mfa == 2 pero un credential_id que no
existe / es de otro user,
When se invoca webauthn.disable,
Then devuelve 404 NOT_FOUND (anti-enumeration).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_disable_not_found(monkeypatch):
    """count_active == 2, soft_disable -> False -> 404 NOT_FOUND."""
    from controllers.webauthn import disable as webauthn_disable

    user = _make_user(status='active')

    wa_svc = MagicMock()
    wa_svc.count_active.return_value = 2
    wa_svc.soft_disable.return_value = False

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
        data={'credential_id': '01900000-0000-7000-8000-000000000099'},
    )
    result = webauthn_disable.Disable(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
