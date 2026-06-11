"""services.permission_checker.check_permission — permiso desconocido.

Given un controller que declarara un permiso que el Lambda no conoce,
When se invoca check_permission('superuser', ...),
Then ApplicationError 500 CONFIGURATION_ERROR (bug de configuracion,
     no del caller) SIN tocar el jwt service.
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import ApplicationError

pytestmark = pytest.mark.unit


def test_permission_checker_unknown_permission_500(monkeypatch):
    from services import permission_checker

    def _never_called(*_a, **_k):
        msg = 'require_active_user no debe invocarse con permiso desconocido'
        raise AssertionError(msg)

    monkeypatch.setattr(
        permission_checker, 'require_active_user', _never_called,
    )

    with pytest.raises(ApplicationError) as exc:
        permission_checker.check_permission(
            'superuser', {'authorization': 'Bearer x'}, action='GetAll',
        )

    assert exc.value.status_code == 500
    assert exc.value.code == 'CONFIGURATION_ERROR'
