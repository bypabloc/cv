"""AC-11: register-options -> 200 con challenge_id + options + persiste challenge.

Given un user autenticado,
When se invoca webauthn.register-options,
Then construye options + persiste el challenge en DDB y devuelve
  challenge_id + options.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_register_options_ok(monkeypatch):
    """AC-11: 200 con challenge_id + options; challenge persistido."""
    from controllers.webauthn import register_options

    user = _make_user(status='active')

    options = {'challenge': 'b64', 'rp': {'id': 'the-full-stack.com'}}
    state = {'opaque': 'state'}
    webauthn_svc = MagicMock()
    webauthn_svc.build_register_options.return_value = (options, state)
    challenge_svc = MagicMock()

    monkeypatch.setattr(
        register_options,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        register_options,
        'WebauthnService',
        lambda _c: webauthn_svc,
    )
    monkeypatch.setattr(
        register_options,
        'ChallengeService',
        lambda _c: challenge_svc,
    )
    monkeypatch.setattr(
        register_options,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event()
    result = register_options.RegisterOptions(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['options'] == options
    assert isinstance(result['data']['challenge_id'], str)
    challenge_svc.put.assert_called_once()
    assert challenge_svc.put.call_args.kwargs['kind'] == 'register'
    assert challenge_svc.put.call_args.kwargs['state'] == state
