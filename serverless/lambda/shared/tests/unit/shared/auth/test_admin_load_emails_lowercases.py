"""
Given un SSM con 'A@X.com',
When se llama load_admin_emails(ttl=300),
Then el email se normaliza a minusculas: frozenset({'a@x.com'}).
"""

import pytest
from shared.auth.admin import load_admin_emails

pytestmark = pytest.mark.unit


def test_load_admin_emails_lowercases_addresses(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        lambda *a, **k: 'A@X.com',
    )

    # Act
    result = load_admin_emails(ttl=300)

    # Assert
    assert result == frozenset({'a@x.com'})
