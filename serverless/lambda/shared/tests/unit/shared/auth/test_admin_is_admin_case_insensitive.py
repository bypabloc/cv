"""
Given una whitelist SSM con 'a@x.com',
When se llama is_admin('A@X.com') (distinto case),
Then retorna True (comparacion case-insensitive).
"""

import pytest
from shared.auth.admin import is_admin

pytestmark = pytest.mark.unit


def test_is_admin_is_case_insensitive(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        lambda *a, **k: 'a@x.com',
    )

    # Act
    result = is_admin('A@X.com')

    # Assert
    assert result is True
