"""
Given un modelo con TableMeta,
When se llama .create_table() / .ensure_table() bajo mock_aws,
Then la tabla queda creada con su KeySchema, TTL y GSI (AC-9).
"""

from __future__ import annotations

import pytest

from shared.dynamodb import TrackingEventItem


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_create_table_builds_key_schema_from_meta() -> None:
    """create_table() crea la tabla con el KeySchema del TableMeta."""
    # Act
    TrackingEventItem.create_table()

    # Assert
    description = TrackingEventItem.describe_table()
    assert description is not None
    assert description['KeySchema'] == [
        {'AttributeName': 'session_id', 'KeyType': 'HASH'},
        {'AttributeName': 'page_id', 'KeyType': 'RANGE'},
    ]


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_create_table_enables_ttl_from_meta() -> None:
    """create_table() activa el TTL declarado en el TableMeta."""
    # Act
    TrackingEventItem.create_table()

    # Assert
    assert TrackingEventItem._ttl_attribute() == 'expires_at'


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_create_table_creates_declared_gsi() -> None:
    """create_table() crea el GSI declarado en el TableMeta."""
    # Act
    TrackingEventItem.create_table()

    # Assert
    description = TrackingEventItem.describe_table()
    gsi_names = {
        idx['IndexName']
        for idx in description.get('GlobalSecondaryIndexes', [])
    }
    assert gsi_names == {'niche-created_at-index'}


@pytest.mark.usefixtures('mock_aws_no_tables')
def test_ensure_table_is_idempotent() -> None:
    """ensure_table() crea si falta y no falla si ya existe."""
    # Act
    TrackingEventItem.ensure_table()
    TrackingEventItem.ensure_table()

    # Assert
    assert TrackingEventItem.table_exists() is True
