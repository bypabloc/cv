"""login-options sin credentials -> 404 NO_WEBAUTHN_CREDENTIALS.

Given un user activo SIN credentials WebAuthn,
When se invoca webauthn.login-options,
Then devuelve 404 NO_WEBAUTHN_CREDENTIALS (anti-enumeration).
"""

from unittest.mock import MagicMock

from .._helpers import _make_temp_event, _make_user


def test_webauthn_login_options_no_credentials(monkeypatch):
    """Sin credentials -> 404 NO_WEBAUTHN_CREDENTIALS."""
    from controllers.webauthn import login_options

    user = _make_user(email='visitor@example.com', status='active')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    webauthn_svc = MagicMock()
    webauthn_svc.has_credentials.return_value = False

    monkeypatch.setattr(login_options, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        login_options,
        'WebauthnService',
        lambda _c: webauthn_svc,
    )
    monkeypatch.setattr(
        login_options,
        'ChallengeService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        login_options,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_temp_event(data={'email': 'visitor@example.com'})
    result = login_options.LoginOptions(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NO_WEBAUTHN_CREDENTIALS'
