"""Controller con user NO-admin -> AdminAuthzError 404 (anti-enumeration).

Given un user autenticado cuyo email NO esta en la whitelist
(require_admin REAL contra ADMIN_EMAILS del conftest),
When se ejecuta catalogs.run(),
Then AdminAuthzError 404 NOT_FOUND se propaga y el service NO se llama.
"""

from unittest.mock import MagicMock

import pytest
from shared.auth.admin import AdminAuthzError

from ._helpers import _make_admin_user, _make_authed_event


def test_controller_non_admin_404(monkeypatch):
    from controllers import _base
    from services import catalog_service

    non_admin = _make_admin_user(email='visitor@example.com')
    monkeypatch.setattr(
        _base, 'require_active_user', lambda *_a, **_k: non_admin,
    )
    service_mock = MagicMock()
    monkeypatch.setattr(catalog_service, 'catalogs', service_mock)

    from controllers.content import catalogs as ctl

    event = _make_authed_event(data={})
    with pytest.raises(AdminAuthzError) as exc:
        ctl.Catalogs(event=event).run()

    assert exc.value.status_code == 404
    assert exc.value.code == 'NOT_FOUND'
    service_mock.assert_not_called()
