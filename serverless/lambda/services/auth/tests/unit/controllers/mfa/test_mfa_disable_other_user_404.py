"""AC-5b: disable de un metodo que no existe para el user -> 404 NOT_FOUND.

Given un metodo que no esta activo para el user (has_active_method=False),
When se invoca mfa.disable,
Then devuelve 404 NOT_FOUND (no revela existencia ajena).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_disable_other_user_404(monkeypatch):
    """AC-5b: metodo no activo para el user -> 404 NOT_FOUND."""
    from controllers.mfa import disable

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.has_active_method.return_value = False

    monkeypatch.setattr(
        disable,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(disable, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(disable, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(disable, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'totp'})
    result = disable.Disable(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
    mfa_svc.count_active.assert_not_called()
