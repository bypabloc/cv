"""Cada operation usa SU endpoint de rate-limit declarado.

Given guards de auth/admin mockeados,
When se ejecuta publish.dispatch.run(),
Then RateLimitService.check_or_raise recibe el endpoint
'/cv#publish.dispatch' (key estricta del trigger de CI).
"""

from unittest.mock import MagicMock

from ._helpers import _make_admin_user, _make_authed_event


def test_controller_rate_limit_endpoint(monkeypatch):
    from controllers import _base
    from services import permission_checker, publish_service

    monkeypatch.setattr(
        permission_checker,
        'require_active_user',
        lambda *_a, **_k: _make_admin_user(),
    )
    rate_limit = MagicMock()
    monkeypatch.setattr(_base, 'RateLimitService', lambda _c: rate_limit)
    monkeypatch.setattr(
        publish_service,
        'dispatch',
        MagicMock(return_value={'dispatched': True}),
    )

    from controllers.publish import dispatch as ctl

    event = _make_authed_event(data={}, ip='203.0.113.77', country='PE')
    result = ctl.Dispatch(event=event).run()

    assert result['is_valid'] is True
    rate_limit.check_or_raise.assert_called_once_with(
        ip='203.0.113.77',
        endpoint='/cv#publish.dispatch',
        country='PE',
    )
