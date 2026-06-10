"""require_admin_user con email en la whitelist -> pasa sin error.

Given un user cuyo email SI esta en la whitelist (ADMIN_EMAILS del
conftest),
When se invoca require_admin_user,
Then no levanta (retorna None).
"""

from unittest.mock import MagicMock


def test_admin_guard_admin_ok():
    from services import admin_guard

    user = MagicMock(id='u1', email='admin@example.com')

    result = admin_guard.require_admin_user(user, ip='203.0.113.10')

    assert result is None
