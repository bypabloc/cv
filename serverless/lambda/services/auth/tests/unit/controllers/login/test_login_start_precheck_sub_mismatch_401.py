"""AC-5: precheck sub que no matchea el user existente -> 401 (anti cross-account).

Given un email que existe active PERO el `sub` del precheck NO matchea su
  user.id,
When se invoca login.start,
Then devuelve 401 MISSING_PRECHECK (el precheck se emitio para otro user) y
  NO envia email.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from .._helpers import _make_event_register_start, _make_user


def test_login_start_precheck_sub_mismatch_401(monkeypatch):
    """AC-5: sub del precheck != user.id -> 401 anti cross-account."""
    from controllers.login import start

    user = _make_user(email='visitor@example.com', status='active')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = SimpleNamespace(
        sub='DIFFERENT-USER-ID', jti='x', exp=9999999999, flow='login',
        typ='temp',
    )
    email_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: email_svc)
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_register_start(email='visitor@example.com')
    event['_meta']['authorization'] = 'Bearer PRECHECK-TEMP'
    result = start.Start(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4003
    assert result['status'] == 401
    assert result['data']['error'] == 'MISSING_PRECHECK'
    email_svc.publish_unified.assert_not_called()
