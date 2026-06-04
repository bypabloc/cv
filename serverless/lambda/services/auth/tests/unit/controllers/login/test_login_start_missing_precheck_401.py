"""AC-4: login.start sin precheck valido -> 401 MISSING_PRECHECK.

Given un evento de login.start sin un temp JWT precheck valido (sin header
  Authorization, o con uno que jwt_svc.verify rechaza),
When se invoca login.start,
Then devuelve 401 MISSING_PRECHECK y NO toca user_svc / email_svc.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_login_start_no_authorization_header_401(monkeypatch):
    """AC-4: sin header Authorization -> 401 MISSING_PRECHECK."""
    from controllers.login import start

    user_svc = MagicMock()
    jwt_svc = MagicMock()
    email_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: email_svc)
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())

    # Sin authorization en _meta: el precheck falta -> 401.
    event = _make_event_register_start(email='visitor@example.com')
    result = start.Start(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4003
    assert result['status'] == 401
    assert result['data']['error'] == 'MISSING_PRECHECK'
    user_svc.get_by_email.assert_not_called()
    user_svc.create_pending.assert_not_called()
    email_svc.publish_unified.assert_not_called()


def test_login_start_invalid_precheck_token_401(monkeypatch):
    """AC-4: header con un temp que verify rechaza -> 401 MISSING_PRECHECK."""
    from controllers.login import start
    from shared.auth.jwt import JwtInvalidError

    user_svc = MagicMock()
    jwt_svc = MagicMock()
    jwt_svc.verify.side_effect = JwtInvalidError('bad')
    email_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: email_svc)
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_register_start(email='visitor@example.com')
    event['_meta']['authorization'] = 'Bearer BAD'
    result = start.Start(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4003
    assert result['status'] == 401
    assert result['data']['error'] == 'MISSING_PRECHECK'
    user_svc.get_by_email.assert_not_called()
    user_svc.create_pending.assert_not_called()
    email_svc.publish_unified.assert_not_called()
