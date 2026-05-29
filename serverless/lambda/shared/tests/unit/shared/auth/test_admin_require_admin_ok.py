"""
Given una whitelist SSM con 'a@x.com,b@y.com',
When se llama require_admin('a@x.com') (email admin),
Then retorna None sin levantar excepcion.
"""

import pytest
from shared.auth.admin import require_admin

pytestmark = pytest.mark.unit


def test_require_admin_returns_none_for_admin(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        lambda *a, **k: 'a@x.com,b@y.com',
    )

    # Act
    result = require_admin('a@x.com')

    # Assert
    assert result is None
