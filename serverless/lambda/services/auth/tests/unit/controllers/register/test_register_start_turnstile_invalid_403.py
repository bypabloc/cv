"""AC-12: Turnstile invalido -> levanta TurnstileError (HTTP 403).

Given un cf_turnstile_response invalido,
When se invoca register.start,
Then verify_turnstile_token levanta TurnstileError; http_handler la
mapea a 403.
"""

from unittest.mock import MagicMock

import pytest

from .._helpers import _make_event_register_start


def test_register_start_turnstile_invalid_403(monkeypatch):
    """AC-12: Turnstile fail -> propaga TurnstileError."""
    from controllers.register import start
    from shared.core.exceptions import TurnstileError

    monkeypatch.setattr(start, 'UserService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())

    def _fail_turnstile(*_a, **_k):
        raise TurnstileError('invalid', code='CAPTCHA_INVALID')

    monkeypatch.setattr(start, 'verify_turnstile_token', _fail_turnstile)

    event = _make_event_register_start()
    controller = start.Start(event=event)

    with pytest.raises(TurnstileError) as exc_info:
        controller.run()
    assert exc_info.value.code == 'CAPTCHA_INVALID'
    assert exc_info.value.status_code == 403
