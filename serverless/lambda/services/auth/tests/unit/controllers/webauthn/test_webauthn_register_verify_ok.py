"""AC-12: register-verify valido -> 201 + persiste credential + consume challenge.

Given un challenge valido del mismo user + una attestation valida,
When se invoca webauthn.register-verify,
Then valida + persiste el credential y devuelve 201.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_register_verify_ok(monkeypatch):
    """AC-12: attestation valida -> 201 + persist."""
    from controllers.webauthn import register_verify

    user = _make_user(status='active')

    cred_data = {'credential_id': b'\x10' * 16, 'public_key': b'\x20' * 32}
    webauthn_svc = MagicMock()
    webauthn_svc.verify_registration.return_value = cred_data
    challenge_svc = MagicMock()
    challenge_svc.get_and_consume.return_value = {
        'user_id': str(user.id),
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
            'nickname': 'MacBook',
        },
    )
    result = register_verify.RegisterVerify(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 201
    assert result['data']['nickname'] == 'MacBook'
    webauthn_svc.persist_credential.assert_called_once_with(
        user_id=user.id,
        cred_data=cred_data,
        nickname='MacBook',
    )
