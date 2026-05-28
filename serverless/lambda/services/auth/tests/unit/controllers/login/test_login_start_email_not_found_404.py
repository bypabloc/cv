"""AC-5: email no existe -> 404 EMAIL_NOT_FOUND con suggest_register=True.

Given un email que no esta en auth_users,
When se invoca login.start,
Then devuelve is_valid=False, code 4001, status 404, suggest_register=True.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_login_start_email_not_found_404(monkeypatch):
    """AC-5: email no existe -> 404 con suggest_register=True."""
    from controllers.login import start

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = None

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        start, 'verify_turnstile_token',
        lambda *_a, **_k: {'success': True},
    )

    event = _make_event_register_start(email='unknown@example.com')
    controller = start.Start(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'EMAIL_NOT_FOUND'
    assert result['data']['suggest_register'] is True
