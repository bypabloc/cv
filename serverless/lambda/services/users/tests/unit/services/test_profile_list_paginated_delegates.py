"""ProfileService.list_paginated — delega a list_users_paginated.

Given un cursor, page_size y status_filter,
When se invoca list_paginated,
Then delega a list_users_paginated con esos kwargs y devuelve las filas.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_list_paginated_delegates_to_repo(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    user_a = MagicMock(id='a')
    user_b = MagicMock(id='b')
    calls = {}

    def fake_list(_session, *, cursor, page_size, status_filter):
        calls['cursor'] = cursor
        calls['page_size'] = page_size
        calls['status_filter'] = status_filter
        return [user_a, user_b]

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service, 'list_users_paginated', fake_list,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.list_paginated(
        cursor='cur-1', page_size=25, status_filter='active',
    )

    assert result == [user_a, user_b]
    assert calls['cursor'] == 'cur-1'
    assert calls['page_size'] == 25
    assert calls['status_filter'] == 'active'
