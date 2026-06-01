"""register-verify con challenge inexistente/expirado -> 400.

Given un challenge_id que no existe en DDB (get_and_consume -> None),
When se invoca webauthn.register-verify,
Then devuelve 400 WEBAUTHN_CHALLENGE_NOT_FOUND.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_register_verify_challenge_expired(monkeypatch):
    """Challenge ausente -> 400 WEBAUTHN_CHALLENGE_NOT_FOUND."""
    from controllers.webauthn import register_verify

    user = _make_user(status='active')

    webauthn_svc = MagicMock()
    challenge_svc = MagicMock()
    challenge_svc.get_and_consume.return_value = None

    monkeypatch.setattr(
        register_verify,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        register_verify,
        'WebauthnService',
        lambda _c: webauthn_svc,
    )
    monkeypatch.setattr(
        register_verify,
        'ChallengeService',
        lambda _c: challenge_svc,
    )
    monkeypatch.setattr(
        register_verify,
        'AuditService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(
        data={
            'challenge_id': '01900000-0000-7000-8000-000000000001',
            'response': {'id': 'x'},
        },
    )
    result = register_verify.RegisterVerify(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4007
    assert result['status'] == 400
    assert result['data']['error'] == 'WEBAUTHN_CHALLENGE_NOT_FOUND'
    webauthn_svc.verify_registration.assert_not_called()
