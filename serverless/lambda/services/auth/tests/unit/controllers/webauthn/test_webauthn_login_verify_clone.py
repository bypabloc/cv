"""AC-15: login-verify con clone detectado -> 401 WEBAUTHN_CLONE_DETECTED.

Given una assertion cuyo sign_count regreso (WebauthnCloneError),
When se invoca webauthn.login-verify,
Then devuelve 401 WEBAUTHN_CLONE_DETECTED + audit clone_detected (el
  service ya marco el credential disabled).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_temp_event


def test_webauthn_login_verify_clone(monkeypatch):
    """AC-15: clone detected -> 401 + audit."""
    from controllers.webauthn import login_verify
    from shared.auth.webauthn import WebauthnCloneError

    uid = uuid4()
    jwt_svc = MagicMock()
    webauthn_svc = MagicMock()
    webauthn_svc.verify_login.side_effect = WebauthnCloneError(
        'sign_count regression',
        credential_id=b'\x10' * 16,
    )
    challenge_svc = MagicMock()
    challenge_svc.get_and_consume.return_value = {
        'user_id': str(uid),
        'kind': 'login',
        'state': {'s': 1},
    }
    audit_svc = MagicMock()

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
    monkeypatch.setattr(login_verify, 'AuditService', lambda _c: audit_svc)
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
    assert result['code'] == 4004
    assert result['status'] == 401
    assert result['data']['error'] == 'WEBAUTHN_CLONE_DETECTED'
    jwt_svc.issue_access.assert_not_called()
    assert (
        audit_svc.log.call_args.kwargs['event']
        == 'webauthn.login.clone_detected'
    )
