"""
Given una tabla creada por el propio ORM desde su TableMeta,
When check_schema compara el TableMeta contra la tabla real,
Then el SchemaDiff esta in_sync (KeySchema, TTL y GSIs coinciden).
"""

from __future__ import annotations

import pytest
from shared.dynamodb import TrackingEventItem

pytestmark = pytest.mark.integration


def test_base_model_check_schema_in_sync_e2e(dynamodb_tables: None) -> None:
    """check_schema sobre una tabla creada por el ORM reporta in_sync."""
    # Act
    diff = TrackingEventItem.check_schema()

    # Assert
    assert diff.in_sync is True
