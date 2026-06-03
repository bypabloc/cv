"""security.overview sin Authorization -> ApplicationError(401).

Given un evento sin header Authorization,
When se invoca security.overview,
Then require_active_user levanta ApplicationError(401) que el
  http_handler traduce; el controller NO la captura (la deja propagar).
"""

from unittest.mock import MagicMock

import pytest

from .._helpers import _make_authed_event


def test_overview_requires_auth(monkeypatch):
    """Sin Authorization -> ApplicationError(401) propaga."""
    from controllers.security import overview as security_overview
    from shared.core.exceptions import ApplicationError

    monkeypatch.setattr(
        security_overview, 'RateLimitService', lambda _c: MagicMock(),
    )

    event = _make_authed_event(authorization=None)
    with pytest.raises(ApplicationError) as exc:
        security_overview.Overview(event=event).run()

    assert exc.value.status_code == 401
