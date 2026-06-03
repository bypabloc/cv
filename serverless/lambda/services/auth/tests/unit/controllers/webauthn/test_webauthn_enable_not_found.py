"""webauthn.enable de un credential inexistente -> 404 NOT_FOUND.

Given un user activo y un credential_id que no existe / es de otro user,
When se invoca webauthn.enable,
Then devuelve 404 NOT_FOUND (anti-enumeration).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_enable_not_found(monkeypatch):
    """wa_svc.enable -> False -> 404 NOT_FOUND."""
    from controllers.webauthn import enable as webauthn_enable

    user = _make_user(status='active')

    wa_svc = MagicMock()
    wa_svc.enable.return_value = False

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
        data={'credential_id': '01900000-0000-7000-8000-000000000099'},
    )
    result = webauthn_enable.Enable(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
