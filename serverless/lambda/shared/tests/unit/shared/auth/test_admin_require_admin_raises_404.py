"""
Given una whitelist SSM con 'a@x.com,b@y.com',
When se llama require_admin('z@z.com') (email no-admin),
Then levanta AdminAuthzError con status_code 404 y code 'NOT_FOUND'.
"""

import pytest
from shared.auth.admin import AdminAuthzError, require_admin

pytestmark = pytest.mark.unit


def test_require_admin_raises_404_for_non_admin(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        lambda *a, **k: 'a@x.com,b@y.com',
    )

    # Act
    with pytest.raises(AdminAuthzError) as exc:
        require_admin('z@z.com')

    # Assert
    assert exc.value.status_code == 404
    assert exc.value.code == 'NOT_FOUND'
