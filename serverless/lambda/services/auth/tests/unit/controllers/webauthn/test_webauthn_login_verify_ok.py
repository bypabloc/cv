"""AC-14: login-verify valido -> 200 access+refresh.

Given un challenge de login + una assertion valida,
When se invoca webauthn.login-verify,
Then valida + emite access+refresh y consume el challenge.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_temp_event


def test_webauthn_login_verify_ok(monkeypatch):
    """AC-14: assertion valida -> 200 con tokens."""
    from controllers.webauthn import login_verify

    uid = uuid4()
    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())
    webauthn_svc = MagicMock()
    webauthn_svc.verify_login.return_value = b'\x10' * 16
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

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    assert result['data']['expires_in'] == 900
