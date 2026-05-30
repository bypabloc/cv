"""AC-1: en prod el bypass de Turnstile NUNCA aplica.

Given STAGE=prod + cf_turnstile_response vacio + un bypass_token,
When se invoca register.start,
Then verify_captcha_or_bypass levanta TurnstileError(CAPTCHA_INVALID): el
     bypass firmado solo existe en dev/local, prod siempre exige CAPTCHA
     real. http_handler la mapea a 403.
"""

from unittest.mock import MagicMock

import pytest

from .._helpers import _make_event_register_start


def test_register_start_bypass_rejected_in_prod(monkeypatch):
    from controllers.register import start
    from shared.core.exceptions import TurnstileError

    # Arrange: STAGE=prod -> el orquestador real rechaza el bypass.
    monkeypatch.setenv('STAGE', 'prod')
    monkeypatch.setattr(start, 'UserService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())

    # cf vacio + bypass_token presente: en prod igual se rechaza.
    event = _make_event_register_start(
        cf_token='',
        bypass_token='any-token-value',
    )
    controller = start.Start(event=event)

    # Act / Assert
    with pytest.raises(TurnstileError) as exc_info:
        controller.run()

    assert exc_info.value.code == 'CAPTCHA_INVALID'
    assert exc_info.value.status_code == 403
