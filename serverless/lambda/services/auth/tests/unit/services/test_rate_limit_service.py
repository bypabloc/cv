"""RateLimitService — happy + sad path."""

from unittest.mock import MagicMock


def test_check_or_raise_delegates_to_shared(monkeypatch):
    from services import rate_limit_service

    fake_check = MagicMock(return_value=None)
    monkeypatch.setattr(rate_limit_service, 'check_or_raise', fake_check)

    svc = rate_limit_service.RateLimitService(app_config=object())
    svc.check_or_raise(
        ip='203.0.113.10',
        endpoint='/auth#register.start',
        country='CL',
    )

    fake_check.assert_called_once()
    kwargs = fake_check.call_args.kwargs
    assert kwargs['ip'] == '203.0.113.10'
    assert kwargs['endpoint'] == '/auth#register.start'
    assert kwargs['country'] == 'CL'


def test_check_or_raise_propagates_exception(monkeypatch):
    import pytest

    from services import rate_limit_service

    class FakeRLError(Exception):
        pass

    def _raise(**_kw):
        raise FakeRLError('exceeded')

    monkeypatch.setattr(rate_limit_service, 'check_or_raise', _raise)

    svc = rate_limit_service.RateLimitService(app_config=object())

    with pytest.raises(FakeRLError):
        svc.check_or_raise(ip='203.0.113.10', endpoint='/auth#login.start')
