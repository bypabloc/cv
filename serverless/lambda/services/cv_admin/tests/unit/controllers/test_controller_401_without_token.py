"""Controller sin Authorization -> ApplicationError 401 (propagada).

Given un evento sin Authorization en _meta (require_active_user REAL),
When se ejecuta catalogs.run(),
Then ApplicationError 401 MISSING_AUTHORIZATION se propaga (la mapea
http_handler) ANTES de tocar admin guard / rate-limit / DB.
"""

import pytest
from shared.core.exceptions import ApplicationError

from ._helpers import _make_authed_event


def test_controller_401_without_token():
    from controllers.content import catalogs as ctl

    event = _make_authed_event(data={}, authorization=None)

    with pytest.raises(ApplicationError) as exc:
        ctl.Catalogs(event=event).run()

    assert exc.value.status_code == 401
    assert exc.value.code == 'MISSING_AUTHORIZATION'
