"""register-verify con attestation invalida -> 400 WEBAUTHN_REGISTRATION_FAILED.

Given un challenge valido pero verify_registration levanta WebauthnVerifyError,
When se invoca webauthn.register-verify,
Then devuelve 400 WEBAUTHN_REGISTRATION_FAILED.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_register_verify_attestation_invalid(monkeypatch):
    """Attestation invalida -> 400 WEBAUTHN_REGISTRATION_FAILED."""
    from controllers.webauthn import register_verify
    from shared.auth.webauthn import WebauthnVerifyError

    user = _make_user(status='active')

    webauthn_svc = MagicMock()
    webauthn_svc.verify_registration.side_effect = WebauthnVerifyError(
        'bad attestation',
    )
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
        },
    )
    result = register_verify.RegisterVerify(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 1002
    assert result['status'] == 400
    assert result['data']['error'] == 'WEBAUTHN_REGISTRATION_FAILED'
    webauthn_svc.persist_credential.assert_not_called()
