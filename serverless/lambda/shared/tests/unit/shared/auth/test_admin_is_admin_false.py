"""
Given una whitelist SSM con 'a@x.com,b@y.com',
When se llama is_admin('z@z.com') (email fuera de la lista),
Then retorna False.
"""

import pytest
from shared.auth.admin import is_admin

pytestmark = pytest.mark.unit


def test_is_admin_returns_false_for_unlisted_email(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        lambda *a, **k: 'a@x.com,b@y.com',
    )

    # Act
    result = is_admin('z@z.com')

    # Assert
    assert result is False
