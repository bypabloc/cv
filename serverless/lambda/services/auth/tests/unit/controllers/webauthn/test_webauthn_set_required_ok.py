"""webauthn.set-required marca un passkey requerido -> 204.

Given un user activo y un credential_id valido,
When se invoca webauthn.set-required con required=True,
Then marca el credential como requerido y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_set_required_ok(monkeypatch):
    """wa_svc.set_required -> True -> 204."""
    from controllers.webauthn import set_required as webauthn_set_required

    user = _make_user(status='active')

    wa_svc = MagicMock()
    wa_svc.set_required.return_value = True

    monkeypatch.setattr(
        webauthn_set_required,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        webauthn_set_required,
        'WebauthnService',
        lambda _c: wa_svc,
    )
    monkeypatch.setattr(
        webauthn_set_required,
        'AuditService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        webauthn_set_required,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(
        data={
            'credential_id': '01900000-0000-7000-8000-000000000001',
            'required': True,
        },
    )
    result = webauthn_set_required.SetRequired(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    assert result['data'] == {}
    wa_svc.set_required.assert_called_once_with(
        user_id=user.id,
        record_id='01900000-0000-7000-8000-000000000001',
        required=True,
    )
