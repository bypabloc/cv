"""
Given un get_secret_by_name mockeado con ttl=0 (cache expirado),
When se llama load_admin_emails(ttl=0) dos veces,
Then el SSM se consulta en ambas llamadas: call_count == 2.
"""

from unittest.mock import MagicMock

import pytest
from shared.auth.admin import load_admin_emails

pytestmark = pytest.mark.unit


def test_load_admin_emails_refreshes_when_ttl_zero(monkeypatch):
    # Arrange
    mock_secret = MagicMock(return_value='a@x.com,b@y.com')
    monkeypatch.setattr(
        'shared.auth.admin.get_secret_by_name',
        mock_secret,
    )

    # Act
    load_admin_emails(ttl=0)
    load_admin_emails(ttl=0)

    # Assert
    assert mock_secret.call_count == 2
