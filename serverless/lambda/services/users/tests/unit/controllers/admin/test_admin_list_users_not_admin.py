"""AC-11: admin.list-users de un caller no-admin -> AdminAuthzError.

Given un caller cuyo email NO esta en la whitelist admin,
When se invoca admin.list-users,
Then require_admin_user lanza AdminAuthzError('NOT_FOUND').
"""

from unittest.mock import MagicMock

import pytest
from shared.auth import AdminAuthzError

from .._helpers import _make_authed_event, _make_user


def test_admin_list_users_not_admin(monkeypatch):
    """no-admin -> AdminAuthzError (anti-enumeration NOT_FOUND)."""
    from controllers.admin import list_users as ctl

    actor = _make_user(user_id='actor-id')

    def _deny(*_a, **_k):
        raise AdminAuthzError('NOT_FOUND')

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', _deny)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event()

    with pytest.raises(AdminAuthzError):
        ctl.ListUsers(event=event).run()
