"""setup-totp con rate-limit excedido -> RateLimitExceededError propaga.

Given un IP que excedio el rate-limit del endpoint,
When se invoca mfa.setup-totp,
Then RateLimitService.check_or_raise levanta y el controller no ejecuta.
"""

from unittest.mock import MagicMock

import pytest

from .._helpers import _make_authed_event


def test_mfa_setup_totp_rate_limited(monkeypatch):
    """Rate-limit excedido -> excepcion del rate-limit propaga."""
    from controllers.mfa import setup_totp
    from shared.rate_limit.exceptions import RateLimitExceededError

    rl_svc = MagicMock()
    rl_svc.check_or_raise.side_effect = RateLimitExceededError(
        'rate limited',
        retry_after_seconds=60,
    )
    monkeypatch.setattr(setup_totp, 'RateLimitService', lambda _c: rl_svc)
    monkeypatch.setattr(
        setup_totp,
        'require_active_user',
        lambda *_a, **_k: MagicMock(),
    )

    event = _make_authed_event()
    with pytest.raises(RateLimitExceededError):
        setup_totp.SetupTotp(event=event).run()
