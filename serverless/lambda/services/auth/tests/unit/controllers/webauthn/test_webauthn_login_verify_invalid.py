"""login-verify con assertion invalida -> 401 WEBAUTHN_VERIFY_FAILED.

Given una assertion invalida (WebauthnVerifyError, no clone),
When se invoca webauthn.login-verify,
Then devuelve 401 WEBAUTHN_VERIFY_FAILED.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_temp_event


def test_webauthn_login_verify_invalid(monkeypatch):
    """Assertion invalida -> 401 WEBAUTHN_VERIFY_FAILED."""
    from controllers.webauthn import login_verify
    from shared.auth.webauthn import WebauthnVerifyError

    uid = uuid4()
    jwt_svc = MagicMock()
    webauthn_svc = MagicMock()
    webauthn_svc.verify_login.side_effect = WebauthnVerifyError('bad sig')
    challenge_svc = MagicMock()
    challenge_svc.get_and_consume.return_value = {
        'user_id': str(uid),
        'kind': 'login',
        'state': {'s': 1},
    }

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
    assert result['code'] == 4004
    assert result['status'] == 401
    assert result['data']['error'] == 'WEBAUTHN_VERIFY_FAILED'
    jwt_svc.issue_access.assert_not_called()
