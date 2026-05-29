"""setup-totp sin Authorization -> ApplicationError(401).

Given un evento sin header Authorization,
When se invoca mfa.setup-totp,
Then require_active_user levanta ApplicationError(401) que el http_handler
  traduce; el controller NO la captura (la deja propagar).
"""

from unittest.mock import MagicMock

import pytest

from .._helpers import _make_authed_event


def test_mfa_setup_totp_no_auth(monkeypatch):
    """Sin Authorization -> ApplicationError(401) propaga."""
    from controllers.mfa import setup_totp
    from shared.core import ApplicationError

    monkeypatch.setattr(setup_totp, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(authorization=None)
    with pytest.raises(ApplicationError) as exc:
        setup_totp.SetupTotp(event=event).run()

    assert exc.value.status_code == 401
