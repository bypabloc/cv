"""
Given una tabla creada (o no) bajo mock_aws,
When se llama .table_exists(),
Then devuelve True si existe, False si no (AC-9).
"""

from __future__ import annotations

import pytest
from shared.dynamodb.models import ContactItem


@pytest.mark.usefixtures('dynamodb_tables')
def test_table_exists_true_when_created() -> None:
    """table_exists() es True para una tabla creada por el fixture."""
    # Act / Assert
    assert ContactItem.table_exists() is True


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_table_exists_false_when_absent() -> None:
    """table_exists() es False si la tabla no fue creada."""
    # Act / Assert
    assert ContactItem.table_exists() is False


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_describe_table_returns_none_when_absent() -> None:
    """describe_table() devuelve None si la tabla no existe."""
    # Act / Assert
    assert ContactItem.describe_table() is None
