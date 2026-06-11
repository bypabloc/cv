"""require_admin_user con email fuera de la whitelist -> 404.

Given un user cuyo email NO esta en la whitelist SSM admin-emails,
When se invoca require_admin_user,
Then AdminAuthzError (404 NOT_FOUND, anti-enumeration).
"""

from unittest.mock import MagicMock

import pytest
from shared.auth.admin import AdminAuthzError


def test_admin_guard_non_admin_404(monkeypatch):
    from services import admin_guard

    def _deny(_email):
        raise AdminAuthzError('NOT_FOUND')

    monkeypatch.setattr(admin_guard, 'require_admin', _deny)
    user = MagicMock(id='u1', email='visitor@example.com')

    with pytest.raises(AdminAuthzError) as exc:
        admin_guard.require_admin_user(user, ip='203.0.113.10')

    assert exc.value.status_code == 404
    assert exc.value.code == 'NOT_FOUND'
