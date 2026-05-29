"""RateLimitService.check_or_raise — turnstile_validated siempre False.

Given un endpoint JWT-authed de users,
When se invoca check_or_raise,
Then delega a shared.rate_limit.check_or_raise con turnstile_validated=False.
"""


def test_rate_limit_check_passes_turnstile_validated_false(monkeypatch):
    from services import rate_limit_service

    calls = {}

    def fake_check(*, ip, endpoint, country, turnstile_validated):
        calls['ip'] = ip
        calls['endpoint'] = endpoint
        calls['country'] = country
        calls['turnstile_validated'] = turnstile_validated

    monkeypatch.setattr(rate_limit_service, 'check_or_raise', fake_check)

    svc = rate_limit_service.RateLimitService(app_config=object())
    svc.check_or_raise(
        ip='1.1.1.1', endpoint='/users#profile.update', country='CL',
    )

    assert calls['ip'] == '1.1.1.1'
    assert calls['endpoint'] == '/users#profile.update'
    assert calls['country'] == 'CL'
    assert calls['turnstile_validated'] is False
