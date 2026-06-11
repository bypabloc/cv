"""services.permission_checker.check_permission — concede 'admin'.

Given require_active_user mockeado devolviendo un user cuyo email esta
     en la whitelist (ADMIN_EMAILS del conftest),
When se invoca check_permission('admin', meta, action=...),
Then devuelve ese user (el subject de la fase Authorize) y paso el
     authorization del meta al jwt service.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


def test_permission_checker_grants_admin(monkeypatch):
    from services import permission_checker

    admin = MagicMock(id='u1', email='admin@example.com')
    received: dict = {}

    def _fake_require_active_user(authorization, *, app_config):
        received['authorization'] = authorization
        return admin

    monkeypatch.setattr(
        permission_checker, 'require_active_user', _fake_require_active_user,
    )

    meta = {'authorization': 'Bearer FAKE-JWT', 'ip': '203.0.113.9'}
    subject = permission_checker.check_permission(
        'admin', meta, action='GetAll',
    )

    assert subject is admin
    assert received == {'authorization': 'Bearer FAKE-JWT'}
