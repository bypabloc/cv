"""register-verify con challenge de otro user -> 404 NOT_FOUND.

Given un challenge cuyo user_id difiere del autenticado,
When se invoca webauthn.register-verify,
Then devuelve 404 NOT_FOUND (anti-enumeration).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_authed_event, _make_user


def test_webauthn_register_verify_other_user_404(monkeypatch):
    """Challenge de otro user -> 404 NOT_FOUND."""
    from controllers.webauthn import register_verify

    user = _make_user(status='active')

    webauthn_svc = MagicMock()
    challenge_svc = MagicMock()
    challenge_svc.get_and_consume.return_value = {
        'user_id': str(uuid4()),
        'kind': 'register',
        'state': {'s': 1},
    }

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
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
    webauthn_svc.verify_registration.assert_not_called()
