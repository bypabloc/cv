"""AC-D2: email pending -> re-emite el email unificado (ya NO 409).

Given un email que existe con status pending,
When se invoca login.start (fusion register->login, bloque D),
Then re-emite code + magic-link, publica el email y devuelve un temp_token
  (flow login, step 1) + created=False. (Ya NO devuelve 409.)
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_login_start_email_pending_reemits(monkeypatch):
    """AC-D2: email pending -> re-emite email + created=False."""
    from controllers.login import start
    from shared.db.models.auth.enums import AuthUserStatus

    pending_user = MagicMock()
    pending_user.id = 'usr-pending'
    pending_user.email = 'pending@example.com'
    pending_user.status = AuthUserStatus.PENDING
    user_svc = MagicMock()
    user_svc.get_by_email.return_value = pending_user

    code_svc = MagicMock()
    code_svc.generate_and_persist.return_value = ('CODE5678', MagicMock())
    link_svc = MagicMock()
    link_svc.generate_and_persist.return_value = ('TOKEN-ABC', MagicMock())
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('TEMP-JWT', MagicMock())
    jwt_svc.verify.return_value = SimpleNamespace(
        sub='usr-pending', jti='precheck-jti', exp=9999999999, flow='login',
        typ='temp',
    )
    email_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: link_svc)
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: email_svc)
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_register_start(email='pending@example.com')
    event['_meta']['authorization'] = 'Bearer PRECHECK-TEMP'
    result = start.Start(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['created'] is False
    assert result['data']['temp_token'] == 'TEMP-JWT'
    user_svc.create_pending.assert_not_called()
    user_svc.invalidate_active_codes_and_links.assert_called_once()
    email_svc.publish_unified.assert_called_once()
