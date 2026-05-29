"""
Given un get_secret_by_name mockeado con TTL vigente (300),
When se llama load_admin_emails(ttl=300) dos veces,
Then el SSM se consulta una sola vez (cache hit): call_count == 1.
"""

from unittest.mock import MagicMock

import pytest
from shared.auth.admin import load_admin_emails

pytestmark = pytest.mark.unit


def test_load_admin_emails_caches_within_ttl(monkeypatch):
    # Arrange
    mock_secret = MagicMock(return_value='a@x.com,b@y.com')
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        mock_secret,
    )

    # Act
    load_admin_emails(ttl=300)
    load_admin_emails(ttl=300)

    # Assert
    assert mock_secret.call_count == 1
