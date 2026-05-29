"""AC-4: temp_token valido + password >= 12 -> persiste hash + emite tokens.

Given un temp_token valido y una password de 12+ chars,
When se invoca verify.set-password,
Then upserta el hash, cierra el flujo y devuelve access+refresh.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_set_password, _make_jwt_claims, _make_user


def test_verify_set_password_ok(monkeypatch):
    """AC-4: set-password OK -> tokens."""
    from controllers.verify import set_password

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='register')
    user = _make_user(user_id=uid, status='active')

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    flow_svc = MagicMock()
    flow_svc.terminate_flow.return_value = (
        'ACCESS-JWT',
        'REFRESH-JWT',
        uuid4(),
    )

    audit_svc = MagicMock()
    rl_svc = MagicMock()

    monkeypatch.setattr(set_password, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(set_password, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(set_password, 'FlowService', lambda _c: flow_svc)
    monkeypatch.setattr(set_password, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(set_password, 'RateLimitService', lambda _c: rl_svc)
    monkeypatch.setattr(set_password, 'hash_password', lambda _p: 'HASH')

    event = _make_event_set_password(password='a-very-strong-pass-1')
    controller = set_password.SetPassword(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    user_svc.set_password_hash.assert_called_once_with(
        user_id=str(uid),
        password_hash='HASH',
    )
