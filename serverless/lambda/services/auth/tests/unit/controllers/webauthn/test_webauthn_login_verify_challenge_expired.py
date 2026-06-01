"""login-verify con challenge ausente -> 400 WEBAUTHN_CHALLENGE_NOT_FOUND.

Given un challenge_id que no existe (get_and_consume -> None),
When se invoca webauthn.login-verify,
Then devuelve 400 WEBAUTHN_CHALLENGE_NOT_FOUND.
"""

from unittest.mock import MagicMock

from .._helpers import _make_temp_event


def test_webauthn_login_verify_challenge_expired(monkeypatch):
    """Challenge ausente -> 400 WEBAUTHN_CHALLENGE_NOT_FOUND."""
    from controllers.webauthn import login_verify

    jwt_svc = MagicMock()
    webauthn_svc = MagicMock()
    challenge_svc = MagicMock()
    challenge_svc.get_and_consume.return_value = None

    monkeypatch.setattr(login_verify, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(
        login_verify,
        'WebauthnService',
        lambda _c: webauthn_svc,
    )
    monkeypatch.setattr(
        login_verify,
        'ChallengeService',
        lambda _c: challenge_svc,
    )
    monkeypatch.setattr(login_verify, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        login_verify,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_temp_event(
        data={
            'challenge_id': '01900000-0000-7000-8000-000000000001',
            'response': {'id': 'x'},
        },
    )
    result = login_verify.LoginVerify(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4007
    assert result['status'] == 400
    assert result['data']['error'] == 'WEBAUTHN_CHALLENGE_NOT_FOUND'
    webauthn_svc.verify_login.assert_not_called()
