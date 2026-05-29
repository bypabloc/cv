"""AC-13: admin.list-users con pagina llena setea next_cursor.

Given un admin y 2 users con page_size 2 (len == page_size),
When se invoca admin.list-users,
Then next_cursor es el id del ultimo user de la pagina.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def _user_mock(user_id, email, status, display_name):
    """Mock con .id/.email/.status.value/.created_at.isoformat()/.display_name."""
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.status.value = status
    user.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    user.display_name = display_name
    return user


def test_admin_list_users_paginated(monkeypatch):
    """AC-13: len == page_size -> next_cursor == id del ultimo."""
    from controllers.admin import list_users as ctl

    actor = _make_user(user_id='actor-id')
    u1 = _user_mock('user-1', 'a@example.com', 'active', 'Alice')
    u2 = _user_mock('user-2', 'b@example.com', 'active', 'Bob')

    profile_svc = MagicMock()
    profile_svc.list_paginated.return_value = [u1, u2]

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: actor)
    monkeypatch.setattr(ctl, 'require_admin_user', lambda *_a, **_k: None)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'page_size': 2})
    result = ctl.ListUsers(event=event).run()

    assert result['is_valid'] is True
    assert result['data']['page_size'] == 2
    assert result['data']['total_returned'] == 2
    assert result['data']['next_cursor'] == 'user-2'
