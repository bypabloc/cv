"""
Given un SSM con valor vacio '',
When se llama load_admin_emails(ttl=300),
Then retorna un frozenset vacio (sin admins).
"""

import pytest
from shared.auth.admin import load_admin_emails

pytestmark = pytest.mark.unit


def test_load_admin_emails_empty_value_returns_empty_frozenset(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        lambda *a, **k: '',
    )

    # Act
    result = load_admin_emails(ttl=300)

    # Assert
    assert result == frozenset()
