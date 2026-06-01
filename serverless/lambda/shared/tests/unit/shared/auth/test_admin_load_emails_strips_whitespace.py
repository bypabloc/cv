"""
Given un SSM con ' a@x.com , b@y.com ' (espacios alrededor),
When se llama load_admin_emails(ttl=300),
Then cada email se trimea: frozenset({'a@x.com', 'b@y.com'}).
"""

import pytest
from shared.auth.admin import load_admin_emails

pytestmark = pytest.mark.unit


def test_load_admin_emails_strips_surrounding_whitespace(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        lambda *a, **k: ' a@x.com , b@y.com ',
    )

    # Act
    result = load_admin_emails(ttl=300)

    # Assert
    assert result == frozenset({'a@x.com', 'b@y.com'})
