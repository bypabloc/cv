"""AC-13: rate-limit excedido -> levanta RateLimitExceededError (HTTP 429).

Given una IP que paso el limite del endpoint register.start,
When se invoca register.start,
Then RateLimitService.check_or_raise levanta RateLimitExceededError.
"""

from unittest.mock import MagicMock

import pytest

from .._helpers import _make_event_register_start


def test_register_start_rate_limited_429(monkeypatch):
    """AC-13: rate-limit fail -> propaga RateLimitExceededError."""
    from controllers.register import start
    from shared.core.exceptions import RateLimitExceededError

    rl_svc = MagicMock()
    rl_svc.check_or_raise.side_effect = RateLimitExceededError(
        'limit hit', retry_after_seconds=60,
    )

    monkeypatch.setattr(start, 'UserService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: rl_svc)
    monkeypatch.setattr(
        start, 'verify_turnstile_token',
        lambda *_a, **_k: {'success': True},
    )

    event = _make_event_register_start()
    controller = start.Start(event=event)

    with pytest.raises(RateLimitExceededError) as exc_info:
        controller.run()
    assert exc_info.value.status_code == 429
