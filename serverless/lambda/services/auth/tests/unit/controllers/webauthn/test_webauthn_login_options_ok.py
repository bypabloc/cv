"""AC-13: login-options con credentials -> 200 challenge + options.

Given un user activo con >=1 credential WebAuthn,
When se invoca webauthn.login-options con su email,
Then devuelve challenge_id + options y persiste el challenge.
"""

from unittest.mock import MagicMock

from .._helpers import _make_temp_event, _make_user


def test_webauthn_login_options_ok(monkeypatch):
    """AC-13: user con credentials -> 200 challenge + options."""
    from controllers.webauthn import login_options

    user = _make_user(email='visitor@example.com', status='active')

    options = {'challenge': 'b64', 'allowCredentials': [{'id': 'c1'}]}
    state = {'opaque': 'state'}
    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    webauthn_svc = MagicMock()
    webauthn_svc.has_credentials.return_value = True
    webauthn_svc.build_login_options.return_value = (options, state)
    challenge_svc = MagicMock()

    monkeypatch.setattr(login_options, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        login_options,
        'WebauthnService',
        lambda _c: webauthn_svc,
    )
    monkeypatch.setattr(
        login_options,
        'ChallengeService',
        lambda _c: challenge_svc,
    )
    monkeypatch.setattr(
        login_options,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_temp_event(data={'email': 'visitor@example.com'})
    result = login_options.LoginOptions(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['options'] == options
    assert isinstance(result['data']['challenge_id'], str)
    assert challenge_svc.put.call_args.kwargs['kind'] == 'login'
