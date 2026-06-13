"""RateLimitService pasa turnstile_validated=False SIEMPRE.

Given los endpoints de las operations admin del cv son JWT-authed (sin Turnstile),
When se invoca RateLimitService.check_or_raise,
Then shared.rate_limit.check_or_raise recibe turnstile_validated=False.
"""

from unittest.mock import MagicMock


def test_rate_limit_turnstile_false(monkeypatch):
    from services import rate_limit_service

    check_mock = MagicMock()
    monkeypatch.setattr(rate_limit_service, 'check_or_raise', check_mock)

    rate_limit_service.RateLimitService(object()).check_or_raise(
        ip='203.0.113.10', endpoint='/cv#content', country='CL',
    )

    check_mock.assert_called_once_with(
        ip='203.0.113.10',
        endpoint='/cv#content',
        country='CL',
        turnstile_validated=False,
    )
