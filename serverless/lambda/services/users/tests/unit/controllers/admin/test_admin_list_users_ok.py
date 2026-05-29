"""AC-12: admin.list-users devuelve la pagina de users -> 200.

Given un admin y 2 users con page_size 50,
When se invoca admin.list-users,
Then devuelve 200 con los 2 users serializados y next_cursor None
(len 2 < page_size 50).
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


def test_admin_list_users_ok(monkeypatch):
    """AC-12: 2 users + page_size 50 -> next_cursor None."""
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

    event = _make_authed_event()
    result = ctl.ListUsers(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['page_size'] == 50
    assert result['data']['total_returned'] == 2
    assert result['data']['next_cursor'] is None
    assert result['data']['users'] == [
        {
            'id': 'user-1',
            'email': 'a@example.com',
            'status': 'active',
            'created_at': '2026-01-01T00:00:00+00:00',
            'display_name': 'Alice',
        },
        {
            'id': 'user-2',
            'email': 'b@example.com',
            'status': 'active',
            'created_at': '2026-01-01T00:00:00+00:00',
            'display_name': 'Bob',
        },
    ]
