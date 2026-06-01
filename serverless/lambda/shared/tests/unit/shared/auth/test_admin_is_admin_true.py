"""
Given una whitelist SSM con 'a@x.com,b@y.com',
When se llama is_admin('a@x.com'),
Then retorna True.
"""

import pytest
from shared.auth.admin import is_admin

pytestmark = pytest.mark.unit


def test_is_admin_returns_true_for_listed_email(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        lambda *a, **k: 'a@x.com,b@y.com',
    )

    # Act
    result = is_admin('a@x.com')

    # Assert
    assert result is True
